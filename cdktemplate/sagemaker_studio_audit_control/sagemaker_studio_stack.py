# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import ( 
	aws_iam as iam,
	aws_lambda as _lambda,
	core
)
import os

ROLE_NAME_PREFIX = os.environ["ROLE_NAME_PREFIX"]

class SageMakerStudioStack(core.Stack):

	def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
		super().__init__(scope, id, **kwargs)

	# CloudFormation Parameters

		user_data_scientist_1 = core.CfnParameter(self, "DataScientistFullAccessUsername", 
				type="String",
				description="Username for Data Scientist with full access to Amazon Reviews.",
				allowed_pattern="^[a-zA-Z0-9](-*[a-zA-Z0-9])*",
				default = "data-scientist-full"
			)

		user_data_scientist_2 = core.CfnParameter(self, "DataScientistLimitedAccessUsername", 
				type="String",
				description="Username for Data Scientist with limited access to Amazon Reviews.",
				allowed_pattern="^[a-zA-Z0-9](-*[a-zA-Z0-9])*",
				default = "data-scientist-limited"
			)

		sagemaker_studio_vpc = core.CfnParameter(self, "SageMakerStudioVpcId", 
				type="String",
				description="VPC that SageMaker Studio will use for communication with the EFS volume."
			)

		sagemaker_studio_subnets = core.CfnParameter(self, "SageMakerStudiosubnetIds", 
				type="CommaDelimitedList",
				description="Subnet(s) that SageMaker Studio will use for communication with the EFS volume. Must be in the selected VPC and in different AZs."
			)


		self.template_options.template_format_version = "2010-09-09"
		self.template_options.description = "SageMaker Studio and Studio User Profiles."
		self.template_options.metadata = { "License": "MIT-0" }

	# IAM Users and Roles for Data Scientists

		user_1 = iam.User.from_user_name(self, "DataScientist1IAMUser", 
			user_name = user_data_scientist_1.value_as_string)

		user_2 = iam.User.from_user_name(self, "DataScientist2IAMUser", 
			user_name = user_data_scientist_2.value_as_string)

		data_scientist_role_1 = ROLE_NAME_PREFIX + user_data_scientist_1.value_as_string
		data_scientist_role_2 = ROLE_NAME_PREFIX + user_data_scientist_2.value_as_string

		role_1 = iam.Role.from_role_arn(self, "DataScientistFullIAMRole", 
			role_arn = "arn:aws:iam::{}:role/{}".format(core.Aws.ACCOUNT_ID, data_scientist_role_1)
			)

		role_2 = iam.Role.from_role_arn(self, "DataScientistLimitedIAMRole", 
			role_arn = "arn:aws:iam::{}:role/{}".format(core.Aws.ACCOUNT_ID, data_scientist_role_2)
			)

	# Create SagemMaker Studio Domain (as Custom Resource)

		with open("lambda/sagemaker_studio_domain.py", encoding="utf8") as fp1:
			sagemaker_studio_domain_code = fp1.read()

		sm_default_execution_role = iam.Role(self, "SageMakerStudioDefaultExecutionRole",
			role_name = ROLE_NAME_PREFIX + "Default", 
			assumed_by = iam.ServicePrincipal('sagemaker.amazonaws.com'),
			managed_policies = [iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")]
			)

		sagemaker_domain_execution_role = iam.Role(self, "SageMakerDomainHandlerServiceRole",
			role_name = "SageMakerDomainHandlerServiceRole", 
			assumed_by = iam.ServicePrincipal('lambda.amazonaws.com'),
			managed_policies = [
				iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
			],
			inline_policies = { "SageMakerDomainHandlerRoleInlinePolicy" : iam.PolicyDocument( 
				statements = [
					iam.PolicyStatement(
						effect=iam.Effect.ALLOW,
						actions=[
							"sagemaker:*Domain"
						],
						resources=["arn:aws:sagemaker:{}:{}:domain/*".format(core.Aws.REGION, core.Aws.ACCOUNT_ID)]),
					iam.PolicyStatement(
						effect=iam.Effect.ALLOW,
						actions=[
							"sagemaker:ListDomains"
						],
						resources=["*"]),
					iam.PolicyStatement(
						effect=iam.Effect.ALLOW,
						actions=[
							"iam:PassRole",
							"iam:CreateServiceLinkedRole"
						],
						resources=[sm_default_execution_role.role_arn])
					]
				) 
			}
			)

		# sagemaker_domain_execution_role.attach_inline_policy(sagemaker_domain_inline_policy)

		sagemaker_domain_fn = _lambda.Function(self, "SageMakerDomainHandler", 
			runtime = _lambda.Runtime.PYTHON_3_7,
			code = _lambda.InlineCode.from_inline(sagemaker_studio_domain_code),
			handler = "index.handler",
			role =  sagemaker_domain_execution_role,
			timeout = core.Duration.seconds(600)
		)

		sagemaker_domain = core.CustomResource(self, "SageMakerDomain", 
			service_token = sagemaker_domain_fn.function_arn,
			resource_type = "Custom::SageMakerDomain",
			properties = {
				"SubnetIds": sagemaker_studio_subnets.value_as_list,
				"VpcId" : sagemaker_studio_vpc.value_as_string,
				"DefaultExecutionRole" : sm_default_execution_role.role_arn
			}
		)

		sagemaker_domain_id = sagemaker_domain.get_att("DomainId")
		
	# Create SageMaker Studio User Profiles (as Custom Resources)

		with open("lambda/sagemaker_studio_profile.py", encoding="utf8") as fp2:
			sagemaker_studio_profile_code = fp2.read()

		sagemaker_profile_execution_role = iam.Role(self, "SageMakerUserProfileHandlerServiceRole",
			role_name = "SageMakerUserProfileHandlerServiceRole", 
			assumed_by = iam.ServicePrincipal('lambda.amazonaws.com'),
			managed_policies = [
				iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
			],
			inline_policies = { "SageMakerUserProfileHandlerRoleInlinePolicy" : iam.PolicyDocument( 
				statements = [
					iam.PolicyStatement(
						effect=iam.Effect.ALLOW,
						actions=[
							"sagemaker:*UserProfile"
						],
						resources=["arn:aws:sagemaker:{}:{}:user-profile/*".format(core.Aws.REGION, core.Aws.ACCOUNT_ID)]),
					iam.PolicyStatement(
						effect=iam.Effect.ALLOW,
						actions=[
							"iam:PassRole"
						],
						resources=["arn:aws:iam::{}:role/{}*".format(core.Aws.ACCOUNT_ID, ROLE_NAME_PREFIX)])
					]
				) }

			)

		sagemaker_profile_fn = _lambda.Function(self, "SageMakerUserProfileHandler", 
			runtime = _lambda.Runtime.PYTHON_3_7,
			code = _lambda.InlineCode.from_inline(sagemaker_studio_profile_code),
			handler = "index.handler",
			role =  sagemaker_profile_execution_role,
			timeout = core.Duration.seconds(180)
		)

		sagemaker_profile_full = core.CustomResource(self, "SageMakerUserProfileDataScientistFull", 
			service_token = sagemaker_profile_fn.function_arn,
			resource_type = "Custom::SageMakerStudioUserProfile",
			properties = {
				"DomainId": sagemaker_domain_id,
				"UserProfileName" : user_1.user_name,
				"ExecutionRole" : role_1.role_arn
			} 
		)

		sagemaker_profile_limited = core.CustomResource(self, "SageMakerUserProfileDataScientistLimited", 
			service_token = sagemaker_profile_fn.function_arn,
			resource_type = "Custom::SageMakerStudioUserProfile",
			properties = {
				"DomainId": sagemaker_domain_id,
				"UserProfileName" : user_2.user_name,
				"ExecutionRole" : role_2.role_arn
			} 
		)

		sagemaker_profile_full.node.add_dependency(sagemaker_domain)
		sagemaker_profile_limited.node.add_dependency(sagemaker_domain)