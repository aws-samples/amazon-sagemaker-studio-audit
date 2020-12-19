# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import ( 
	core
)
import os

NESTED_STACK_URL_PREFIX = os.environ["NESTED_STACK_URL_PREFIX"]

class SageMakerStudioAuditControlStack(core.Stack):

	def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
		super().__init__(scope, id, **kwargs)

		global NESTED_STACK_URL_PREFIX
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

		sagemaker_studio_vpc = core.CfnParameter(self, "SageMakerStudioVpcId", 
				type="AWS::EC2::VPC::Id",
				description="VPC that SageMaker Studio will use for communication with the EFS volume."
			)

		sagemaker_studio_subnets = core.CfnParameter(self, "SageMakerStudiosubnetIds", 
				type="List<AWS::EC2::Subnet::Id>",
				description="Subnet(s) that SageMaker Studio will use for communication with the EFS volume. Must be in the selected VPC and in different AZs."
			)


		self.template_options.template_format_version = "2010-09-09"
		self.template_options.description = "\
Control and audit data exploration activities with Amazon SageMaker Studio and AWS Lake Formation."
		self.template_options.metadata = {
			"License": "MIT-0",
			"AWS::CloudFormation::Interface": {
				"ParameterGroups": [
					{
						"Label": { "default": "Data Scientist 1" },
						"Parameters": [ user_data_scientist_1.logical_id, pw_data_scientist_1.logical_id ]
					},
					{
						"Label": { "default": "Data Scientist 2" },
						"Parameters": [ user_data_scientist_2.logical_id, pw_data_scientist_2.logical_id ]
					},
					{
						"Label": { "default": "Amazon Reviews Dataset" },
						"Parameters": [ glue_db_name.logical_id, glue_table_name.logical_id ]
					},
					{
						"Label": { "default": "SageMaker Studio VPC" },
						"Parameters": [ sagemaker_studio_vpc.logical_id, sagemaker_studio_subnets.logical_id ]
					}
				],
				"ParameterLabels": {
					user_data_scientist_1.logical_id: {
						"default": "Username"
					},
					pw_data_scientist_1.logical_id: {
						"default": "Password"
					},
					user_data_scientist_2.logical_id: {
						"default": "Username"
					},
					pw_data_scientist_2.logical_id: {
						"default": "Password"
					},
					glue_db_name.logical_id: {
						"default": "Glue Database Name"
					},
					glue_table_name.logical_id: {
						"default": "Glue Table Name"
					},
					sagemaker_studio_vpc.logical_id: {
						"default": "SageMaker Studio VPC ID"
					},
					sagemaker_studio_subnets.logical_id: {
						"default": "SageMaker Studio Subnet(s) ID"
					}
				}
			}
		}

	# Nested Stacks

		amazon_reviews_dataset = core.CfnStack(self, "AmazonReviewsDatasetStack",
			template_url = NESTED_STACK_URL_PREFIX + "AmazonReviewsDatasetStack.yaml",
			parameters = {
				"GlueDatabaseNameAmazonReviews" : glue_db_name.value_as_string,
				"GlueTableNameAmazonReviews" : glue_table_name.value_as_string
			})

		data_scientist_users = core.CfnStack(self, "DataScientistUsersStack",
			template_url = NESTED_STACK_URL_PREFIX + "DataScientistUsersStack.yaml",
			parameters = {
				"DataScientistFullAccessUsername" : user_data_scientist_1.value_as_string,
				"DataScientistFullAccesspassword" : pw_data_scientist_1.value_as_string,
				"DataScientistLimitedAccessUsername" : user_data_scientist_2.value_as_string,
				"DataScientistLimitedAccesspassword" : pw_data_scientist_2.value_as_string,
				"GlueDatabaseNameAmazonReviews" : glue_db_name.value_as_string,
				"GlueTableNameAmazonReviews" : glue_table_name.value_as_string,
			})

		data_scientist_users.add_depends_on(amazon_reviews_dataset)

		sagemaker_studio = core.CfnStack(self, "SageMakerStudioStack", 
			template_url = NESTED_STACK_URL_PREFIX + "SageMakerStudioStack.yaml",
			parameters = {
				"DataScientistFullAccessUsername" : user_data_scientist_1.value_as_string,	
				"DataScientistLimitedAccessUsername" : user_data_scientist_2.value_as_string,
				"SageMakerStudioVpcId" : sagemaker_studio_vpc.value_as_string,
				"SageMakerStudiosubnetIds" : core.Fn.join(",",sagemaker_studio_subnets.value_as_list)
			})

		sagemaker_studio.add_depends_on(data_scientist_users)
