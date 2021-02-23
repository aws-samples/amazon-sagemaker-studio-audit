# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import ( 
	aws_iam as iam,
	aws_lambda as _lambda,
	# aws_sagemaker as sm,
	core
)
import os

ROLE_NAME_PREFIX = os.environ["ROLE_NAME_PREFIX"]

class SageMakerStudioStack(core.Stack):

	def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
		super().__init__(scope, id, **kwargs)

	# CloudFormation Parameters

		studio_authentication = core.CfnParameter(self, "StudioAuthentication", 
				type="String",
				description="Authentication method for SageMaker Studio.",
				allowed_values=[
					"AWS IAM with IAM users",
					"AWS IAM with AWS account federation (external IdP)"
				],
				default = "AWS IAM with IAM users"
			)

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

		federated_user_data_scientist_1 = core.CfnParameter(self, "FederatedDataScientistFullAccess", 
				type="String",
				description="\
IdP user name for data scientist with full access to Amazon Reviews (e.g., \"username\", or \"username@domain\").",
			)

		federated_user_data_scientist_2 = core.CfnParameter(self, "FederatedDataScientistLimitedAccess", 
				type="String",
				description="\
IdP user name for data scientist with limited access to Amazon Reviews (e.g., \"username\", or \"username@domain\").",
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

	# Conditions for SageMaker Studio authentication

		aws_iam_users = core.CfnCondition(self, "IsIAMUserAuthentication", 
			expression = core.Fn.condition_equals("AWS IAM with IAM users", studio_authentication)
		)

		aws_federation = core.CfnCondition(self, "IsFederatedAuthentication", 
			expression = core.Fn.condition_equals("AWS IAM with AWS account federation (external IdP)", studio_authentication)
		)

	# IAM Users and Roles for Data Scientists

		data_scientist_role_1 = core.Fn.condition_if(
			aws_iam_users.logical_id, 
			user_data_scientist_1.value_as_string, 
			core.Fn.condition_if(aws_federation.logical_id, federated_user_data_scientist_1.value_as_string, "")
		)

		data_scientist_role_2 = core.Fn.condition_if(
			aws_iam_users.logical_id, 
			user_data_scientist_2.value_as_string, 
			core.Fn.condition_if(aws_federation.logical_id, federated_user_data_scientist_2.value_as_string, "")
		)

		role_1 = iam.Role.from_role_arn(self, "DataScientistFullIAMRole", 
			role_arn = f"arn:aws:iam::{core.Aws.ACCOUNT_ID}:role/{ROLE_NAME_PREFIX}{data_scientist_role_1.to_string()}"
			)

		role_2 = iam.Role.from_role_arn(self, "DataScientistLimitedIAMRole", 
			role_arn = f"arn:aws:iam::{core.Aws.ACCOUNT_ID}:role/{ROLE_NAME_PREFIX}{data_scientist_role_2.to_string()}"
			)

	# Create SageMaker Studio Domain (as CfnResource)

		sm_default_execution_role = iam.Role(self, "SageMakerStudioDefaultExecutionRole",
			role_name = ROLE_NAME_PREFIX + "Default", 
			assumed_by = iam.ServicePrincipal('sagemaker.amazonaws.com'),
			managed_policies = [iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")]
			)

		sm_domain = core.CfnResource(self, "SageMakerDomain",
			type = "AWS::SageMaker::Domain",
			properties = {
				"AuthMode" : "IAM",
				"DefaultUserSettings" : {
						"ExecutionRole": sm_default_execution_role.role_arn
					},
				"DomainName" : "default-domain",
				"SubnetIds" : sagemaker_studio_subnets.value_as_list,
				"VpcId" : sagemaker_studio_vpc.value_as_string
			})

		sm_domain_id = sm_domain.ref
		
	# Create SageMaker Studio User Profiles (as CfnResources)

		sm_profile_full = core.CfnResource(self, "SageMakerUserProfileDataScientistFull",
			type = "AWS::SageMaker::UserProfile",
			properties =  {
				"DomainId" : sm_domain_id,
				"Tags" : [{
					"Key" : "studiouserid",
					"Value" : data_scientist_role_1
				}],
				"UserProfileName" : user_data_scientist_1.value_as_string,
				"UserSettings" : {
					"ExecutionRole" : role_1.role_arn,
				}
			})

		sm_profile_limited = core.CfnResource(self, "SageMakerUserProfileDataScientistLimited",
			type = "AWS::SageMaker::UserProfile",
			properties =  {
				"DomainId" : sm_domain_id,
				"Tags" : [{
					"Key" : "studiouserid",
					"Value" : data_scientist_role_2
				}],
				"UserProfileName" : user_data_scientist_2.value_as_string,
				"UserSettings" : {
					"ExecutionRole" : role_2.role_arn,
				}
			})

		sm_profile_full.node.add_dependency(sm_domain)
		sm_profile_limited.node.add_dependency(sm_domain)