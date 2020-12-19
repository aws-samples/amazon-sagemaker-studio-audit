# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import ( 
	aws_iam as iam,
	aws_lakeformation as lf,
	core
)
import os

ROLE_NAME_PREFIX = os.environ["ROLE_NAME_PREFIX"]

class DataScientistUsersStack(core.Stack):

	def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
		super().__init__(scope, id, **kwargs)

	# CloudFormation Parameters

		user_data_scientist_1 = core.CfnParameter(self, "DataScientistFullAccessUsername", 
				type="String",
				description="Username for Data Scientist with full access to Amazon Reviews.",
				allowed_pattern="^[a-zA-Z0-9](-*[a-zA-Z0-9])*",
				default = "data-scientist-full"
			)

		pw_data_scientist_1 = core.CfnParameter(self, "DataScientistFullAccesspassword", 
				type="String",
				description="Password for Data Scientist with full access to Amazon Reviews.", 
				no_echo=True,
				min_length=6
			)

		user_data_scientist_2 = core.CfnParameter(self, "DataScientistLimitedAccessUsername", 
				type="String",
				description="Username for Data Scientist with limited access to Amazon Reviews.",
				allowed_pattern="^[a-zA-Z0-9](-*[a-zA-Z0-9])*",
				default = "data-scientist-limited"
			)

		pw_data_scientist_2 = core.CfnParameter(self, "DataScientistLimitedAccesspassword", 
				type="String",
				description="Password for Data Scientist with limited access to Amazon Reviews.", 
				no_echo=True,
				min_length=6
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

	# IAM Group, Users and Roles for Data Scientists

		user_profile_arn = f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:user-profile/*/${{aws:username}}"

		user_role_arn = f"arn:aws:iam::{core.Aws.ACCOUNT_ID}:role/{ROLE_NAME_PREFIX}{{aws:username}}"

		sm_studio_app_arn = f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/${{aws:username}}/*"

		data_scientist_group_managed_policy = iam.ManagedPolicy(self, "DataScientistGroupPolicy",
			managed_policy_name = "DataScientistGroupPolicy",
			statements = [
				iam.PolicyStatement(
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:DescribeDomain",
						"sagemaker:ListDomains",
						"sagemaker:ListUserProfiles",
						"sagemaker:ListApps"
					],
					resources=["*"]),
				iam.PolicyStatement(
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:CreatePresignedDomainUrl",
						"sagemaker:DescribeUserProfile"
					],
					resources=[user_profile_arn]),
				iam.PolicyStatement(
					effect=iam.Effect.DENY,
					actions = [
						"sagemaker:CreatePresignedDomainUrl",
						"sagemaker:DescribeUserProfile"
					],
					not_resources=[user_profile_arn]),
				iam.PolicyStatement(
					effect=iam.Effect.ALLOW,
					actions=[
						"sagemaker:*App"
					],
					resources=[sm_studio_app_arn]),
				iam.PolicyStatement(
					effect=iam.Effect.DENY,
					actions = [
						"sagemaker:*App"
					],
					not_resources=[sm_studio_app_arn]),	
				iam.PolicyStatement(
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

		data_scientists_group = iam.Group(self, "DataScientistsIAMGroup",
				group_name = "DataScientists",
				managed_policies = [
					iam.ManagedPolicy.from_aws_managed_policy_name("job-function/DataScientist"),
					data_scientist_group_managed_policy
				]
			)

		user_1 = iam.User(self, "DataScientist1IAMUser",
				user_name = user_data_scientist_1.value_as_string, 
				password = core.SecretValue.cfn_parameter(pw_data_scientist_1)
			)

		user_2 = iam.User(self, "DataScientist2IAMUser",
				user_name = user_data_scientist_2.value_as_string, 
				password = core.SecretValue.cfn_parameter(pw_data_scientist_2)
			)

		user_1.add_to_group(data_scientists_group)
		user_2.add_to_group(data_scientists_group)

		data_scientist_role_1 = ROLE_NAME_PREFIX + user_data_scientist_1.value_as_string
		data_scientist_role_2 = ROLE_NAME_PREFIX + user_data_scientist_2.value_as_string

		user_profile_managed_policy = iam.ManagedPolicy(self, "SageMakerUserProfileExecutionPolicy",
			managed_policy_name = "SageMakerUserProfileExecutionPolicy",
			statements = [
				iam.PolicyStatement(
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
					effect=iam.Effect.DENY,
					actions = [
						"sts:AssumeRole"
					],
					resources=["*"]),
				] 
			)

		# user_profile_1_managed_policy = iam.ManagedPolicy(self, "DataScientist1IAMPolicy",
		# 	managed_policy_name = "DataScientist1IAMPolicy",
		# 	statements = [
		# 		iam.PolicyStatement(
		# 			effect=iam.Effect.ALLOW,
		# 			actions = [
		# 				"sagemaker:*App"
		# 			],
		# 			resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_1.value_as_string}/*"]),
		# 		iam.PolicyStatement(
		# 			effect=iam.Effect.DENY,
		# 			actions = [
		# 				"sagemaker:*App"
		# 			],
		# 			not_resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_1.value_as_string}/*"]),	
		# 		]
		# 	)

		# user_profile_2_managed_policy = iam.ManagedPolicy(self, "DataScientist2IAMPolicy",
		# 	managed_policy_name = "DataScientist2IAMPolicy",
		# 	statements = [
		# 		iam.PolicyStatement(
		# 			effect=iam.Effect.ALLOW,
		# 			actions = [
		# 				"sagemaker:*App"
		# 			],
		# 			resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_2.value_as_string}/*"]),
		# 		iam.PolicyStatement(
		# 			effect=iam.Effect.DENY,
		# 			actions = [
		# 				"sagemaker:*App"
		# 			],
		# 			not_resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_2.value_as_string}/*"]),	
		# 		]
		# 	)


		role_1 = iam.Role(self, "DataScientist1IAMRole",
				role_name = data_scientist_role_1, 
				assumed_by = iam.ServicePrincipal('sagemaker.amazonaws.com'),
				description = 'Custom role for user ' + user_data_scientist_1.value_as_string + ".",
				managed_policies = [
					iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAthenaFullAccess"),
					iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
					user_profile_managed_policy,
					# user_profile_1_managed_policy
				],
				inline_policies = { "DataScientist1IAMRoleInlinePolicy" : iam.PolicyDocument( 
					statements = [
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions = [
								"sagemaker:*App"
							],
							resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_1.value_as_string}/*"]),
						iam.PolicyStatement(
							effect=iam.Effect.DENY,
							actions = [
								"sagemaker:*App"
							],
							not_resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_1.value_as_string}/*"]),	
						]
					)
				}
			)

		role_2 = iam.Role(self, "DataScientist2IAMRole",
				role_name = data_scientist_role_2, 
				assumed_by = iam.ServicePrincipal('sagemaker.amazonaws.com'),
				description = 'Custom role for user ' + user_data_scientist_2.value_as_string + ".",
				managed_policies = [
					iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAthenaFullAccess"),
					iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
					user_profile_managed_policy,
					# user_profile_2_managed_policy
				],
				inline_policies = { "DataScientist2IAMRoleInlinePolicy" : iam.PolicyDocument( 
					statements = [
						iam.PolicyStatement(
							effect=iam.Effect.ALLOW,
							actions = [
								"sagemaker:*App"
							],
							resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_2.value_as_string}/*"]),
						iam.PolicyStatement(
							effect=iam.Effect.DENY,
							actions = [
								"sagemaker:*App"
							],
							not_resources=[f"arn:aws:sagemaker:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:app/*/{user_data_scientist_2.value_as_string}/*"]),	
						]
					)
				}
			)

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