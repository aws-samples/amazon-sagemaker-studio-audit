# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import ( 
	aws_iam as iam,
	aws_lakeformation as lf,
	aws_secretsmanager as secretsmanager,
	aws_sso as sso,
	core
)
import os
import json

ROLE_NAME_PREFIX = os.environ["ROLE_NAME_PREFIX"]
ATHENA_QUERY_BUCKET_PREFIX = os.environ["ATHENA_QUERY_BUCKET_PREFIX"]

class DataScientistUsersStack(core.Stack):

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

		user_data_scientist_1 = core.CfnParameter(self, "DataScientistFullAccess", 
				type="String",
				description="Username for Data Scientist with full access to Amazon Reviews.",
				allowed_pattern="^[a-zA-Z0-9](-*[a-zA-Z0-9])*",
				default = "data-scientist-full"
			)

		user_data_scientist_2 = core.CfnParameter(self, "DataScientistLimitedAccess", 
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

		glue_db_name = core.CfnParameter(self, "GlueDatabaseNameAmazonReviews", 
				type="String",
				description="Name of Glue DB to be created for Amazon Reviews.",
				allowed_pattern="[\w-]+",
				default = "amazon_reviews_db"
			)

		glue_table_name = core.CfnParameter(self, "GlueTableNameAmazonReviews", 
				type="String",
				description="Name of Glue Table to be created for Amazon Reviews (Parquet).",
				allowed_pattern="[\w-]+",
				default = "amazon_reviews_parquet"
			)

		self.template_options.template_format_version = "2010-09-09"
		self.template_options.description = "IAM Users and Roles for Data Scientists."
		self.template_options.metadata = { "License": "MIT-0" }

	# Conditions for SageMaker Studio authentication

		aws_iam_users = core.CfnCondition(self, "IsIAMUserAuthentication", 
			expression = core.Fn.condition_equals("AWS IAM with IAM users", studio_authentication)
		)

		aws_federation = core.CfnCondition(self, "IsFederatedAuthentication", 
			expression = core.Fn.condition_equals("AWS IAM with AWS account federation (external IdP)", studio_authentication)
		)

	# IAM Policy for Data Scientists Group, Users and Roles for Data Scientists

		data_scientist_group_managed_policy = iam.ManagedPolicy(self, "DataScientistGroupPolicy",
			managed_policy_name = "DataScientistGroupPolicy",
			statements = [
				iam.PolicyStatement(
					sid = "AmazonSageMakerStudioReadOnly",
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:DescribeDomain",
						"sagemaker:ListDomains",
						"sagemaker:ListUserProfiles",
						"sagemaker:ListApps"
					],
					resources=["*"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerAddTags",
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:AddTags"
					],
					resources=["*"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerAllowedUserProfile",
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:CreatePresignedDomainUrl",
						"sagemaker:DescribeUserProfile"
					],
					resources=["*"],
					conditions = {
						"StringEquals": {
							"sagemaker:ResourceTag/studiouserid": "${aws:username}"
						}
					}),
				iam.PolicyStatement(
					sid = "AmazonSageMakerDeniedUserProfiles",
					effect=iam.Effect.DENY,
					actions = [
						"sagemaker:CreatePresignedDomainUrl",
						"sagemaker:DescribeUserProfile"
					],
					resources=["*"],
					conditions = {
						"StringNotEquals": {
							"sagemaker:ResourceTag/studiouserid": "${aws:username}"
						}
					}),
				iam.PolicyStatement(
					sid = "AmazonSageMakerDeniedServices",
					effect=iam.Effect.DENY,
					actions = [
						"sagemaker:CreatePresignedNotebookInstanceUrl",
						"sagemaker:*NotebookInstance",
						"sagemaker:*NotebookInstanceLifecycleConfig",
						"sagemaker:CreateUserProfile",
						"sagemaker:DeleteDomain",
						"sagemaker:DeleteUserProfile"
					],
					resources=["*"])
				]
			)
		data_scientist_group_managed_policy.node.default_child.cfn_options.condition = aws_iam_users

	# IAM Group and Users for Data Scientists (only for AWS IAM with IAM Users)

		data_scientists_group = iam.Group(self, "DataScientistsIAMGroup",
				group_name = "DataScientists",
				managed_policies = [
					# iam.ManagedPolicy.from_aws_managed_policy_name("job-function/DataScientist"),
					data_scientist_group_managed_policy
				]
			)
		
		data_scientists_group.node.default_child.cfn_options.condition = aws_iam_users
		
		pw_data_scientist_1 = secretsmanager.Secret(self, "DataScientistFullAccesspwd", 
				generate_secret_string = secretsmanager.SecretStringGenerator(),
				removal_policy = core.RemovalPolicy.DESTROY
			)
		pw_data_scientist_1.node.default_child.cfn_options.condition = aws_iam_users

		pw_data_scientist_2 = secretsmanager.Secret(self, "DataScientistLimitedAccesspwd", 
				generate_secret_string = secretsmanager.SecretStringGenerator(),
				removal_policy = core.RemovalPolicy.DESTROY
			)
		pw_data_scientist_2.node.default_child.cfn_options.condition = aws_iam_users


		user_1 = iam.User(self, "DataScientist1IAMUser",
				user_name = user_data_scientist_1.value_as_string, 
				password = core.SecretValue.secrets_manager(pw_data_scientist_1.secret_arn),
			)
		user_1.node.default_child.cfn_options.condition = aws_iam_users

		user_2 = iam.User(self, "DataScientist2IAMUser",
				user_name = user_data_scientist_2.value_as_string, 
				password = core.SecretValue.secrets_manager(pw_data_scientist_2.secret_arn),
			)
		user_2.node.default_child.cfn_options.condition = aws_iam_users

		user_1.add_to_group(data_scientists_group)
		user_2.add_to_group(data_scientists_group)

	# IAM Roles for SageMaker User Profiles

		data_scientist_role_1 = core.Fn.condition_if(
			aws_iam_users.logical_id, 
			user_data_scientist_1, 
			core.Fn.condition_if(aws_federation.logical_id, federated_user_data_scientist_1, "")
		)

		data_scientist_role_2 = core.Fn.condition_if(
			aws_iam_users.logical_id, 
			user_data_scientist_2, 
			core.Fn.condition_if(aws_federation.logical_id, federated_user_data_scientist_2, "")
		)

		user_profile_managed_policy = iam.ManagedPolicy(self, "SageMakerUserProfileExecutionPolicy",
			managed_policy_name = "SageMakerUserProfileExecutionPolicy",
			statements = [
				iam.PolicyStatement(
					sid = "AmazonSageMakerStudioReadOnly",
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:DescribeDomain",
						"sagemaker:ListDomains",
						"sagemaker:ListUserProfiles",
						"sagemaker:ListApps"
					],
					resources=["*"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerAddTags",
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:AddTags"
					],
					resources=["*"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerAllowedUserProfile",
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:DescribeUserProfile"
					],
					resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:user-profile/*/${{aws:PrincipalTag/userprofilename}}"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerDeniedUserProfiles",
					effect=iam.Effect.DENY,
					actions = [
						"sagemaker:DescribeUserProfile"
					],
					not_resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:user-profile/*/${{aws:PrincipalTag/userprofilename}}"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerAllowedApp",
					effect=iam.Effect.ALLOW,
					actions = [
						"sagemaker:*App"
					],
					resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/${{aws:PrincipalTag/userprofilename}}/*"]),
				iam.PolicyStatement(
					sid = "AmazonSageMakerDeniedApps",
					effect=iam.Effect.DENY,
					actions = [
						"sagemaker:*App"
					],
					not_resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/${{aws:PrincipalTag/userprofilename}}/*"]),	
				iam.PolicyStatement(
					sid = "LakeFormationPermissions",
					effect=iam.Effect.ALLOW,
					actions=[
						"lakeformation:GetDataAccess",
						"glue:GetTable",
						"glue:GetTables",
						"glue:SearchTables",
						"glue:GetDatabase",
						"glue:GetDatabases",
						"glue:GetPartitions"
					],
					resources=["*"]),
				iam.PolicyStatement(
					sid = "S3Permissions",
					effect=iam.Effect.ALLOW,
					actions=[
						"s3:CreateBucket",
						"s3:GetObject",
						"s3:PutObject"
					],
					resources=[
						f"arn:aws:s3:::{ATHENA_QUERY_BUCKET_PREFIX}{core.Aws.REGION}-{core.Aws.ACCOUNT_ID}",
						f"arn:aws:s3:::{ATHENA_QUERY_BUCKET_PREFIX}{core.Aws.REGION}-{core.Aws.ACCOUNT_ID}/*"
					]),					
				iam.PolicyStatement(	
					sid ="AmazonSageMakerStudioIAMPassRole",
					effect=iam.Effect.ALLOW,
					actions=[
						"iam:PassRole"
					],
					resources=["*"]),
				iam.PolicyStatement(
					sid = "DenyAssummingOtherIAMRoles",
					effect=iam.Effect.DENY,
					actions = [
						"sts:AssumeRole"
					],
					resources=["*"]),		
				] 
			)

		role_1 = iam.Role(self, "DataScientist1IAMRole",
				role_name = f"{ROLE_NAME_PREFIX}{data_scientist_role_1.to_string()}", 
				assumed_by = iam.ServicePrincipal("sagemaker.amazonaws.com"),
				description = f"Custom role for user {data_scientist_role_1.to_string()}.",
				managed_policies = [
					iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAthenaFullAccess"),
					user_profile_managed_policy
				],
			)

		role_2 = iam.Role(self, "DataScientist2IAMRole",
				role_name = f"{ROLE_NAME_PREFIX}{data_scientist_role_2.to_string()}", 
				assumed_by = iam.ServicePrincipal('sagemaker.amazonaws.com'),
				description = f"Custom role for user {data_scientist_role_2.to_string()}.",
				managed_policies = [
					iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAthenaFullAccess"),
					user_profile_managed_policy
				],
			)

		core.Tags.of(role_1).add("userprofilename", user_data_scientist_1.value_as_string)
		core.Tags.of(role_2).add("userprofilename", user_data_scientist_2.value_as_string)

	# Grant Lake Formation Permissinos for Amazon Reviews Table

		lf_permission_1 = lf.CfnPermissions(self, "LFPermissionDataScientist1", 
			data_lake_principal = lf.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier = role_1.role_arn),
			resource = lf.CfnPermissions.ResourceProperty(
				table_resource = lf.CfnPermissions.TableResourceProperty(
					name = glue_table_name.value_as_string,
					database_name = glue_db_name.value_as_string
				)
			), 
			permissions = ["SELECT"],
			permissions_with_grant_option = ["SELECT"])

		lf_permission_2 = lf.CfnPermissions(self, "LFPermissionDataScientist2", 
			data_lake_principal = lf.CfnPermissions.DataLakePrincipalProperty(data_lake_principal_identifier = role_2.role_arn), 
			resource = lf.CfnPermissions.ResourceProperty(
				table_with_columns_resource = lf.CfnPermissions.TableWithColumnsResourceProperty(
					column_names = ["product_category","product_id","product_parent","product_title","star_rating","review_headline","review_body","review_date"],
					name = glue_table_name.value_as_string,
					database_name = glue_db_name.value_as_string
				)
			), 
			permissions = ["SELECT"],
			permissions_with_grant_option = ["SELECT"])

	# Stack Outputs

		core.CfnOutput(self, "IAMUserDSFull", 
			value=user_1.user_name,
			description="IAM User Data Scientist 1",
			condition=aws_iam_users
			)

		core.CfnOutput(self, "IAMUserDSLimited", 
			value=user_2.user_name, 
			description="IAM User Data Scientist 2",
			condition=aws_iam_users
			)