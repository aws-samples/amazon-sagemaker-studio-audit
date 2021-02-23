# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import ( 
	aws_lakeformation as lf,
	aws_glue as glue,
	aws_s3 as s3,
	aws_iam as iam,
	aws_lambda as _lambda,
	core
)
import os

AMAZON_REVIEWS_BUCKET_ARN = os.environ["AMAZON_REVIEWS_BUCKET_ARN"]

class AmazonReviewsDatasetStack(core.Stack):

	def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
		super().__init__(scope, id, **kwargs)

	# CloudFormation Parameters

		glue_db_name = core.CfnParameter(self, "GlueDatabaseNameAmazonReviews", 
				type="String",
				description="Name of Glue Database to be created for Amazon Reviews.",
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
		self.template_options.description = "Amazon Reviews Dataset."
		self.template_options.metadata = { "License": "MIT-0" }

	# Create Database, Table and Partitions for Amazon Reviews

		amazon_reviews_bucket = s3.Bucket.from_bucket_arn(self, "ImportedAmazonReviewsBucket", AMAZON_REVIEWS_BUCKET_ARN)

		lakeformation_resource = lf.CfnResource(self, "LakeFormationResource", 
			resource_arn = amazon_reviews_bucket.bucket_arn, 
			use_service_linked_role = True)

		cfn_glue_db = glue.CfnDatabase(self, "GlueDatabase", 
			catalog_id = core.Aws.ACCOUNT_ID,
			database_input = glue.CfnDatabase.DatabaseInputProperty(
				name = glue_db_name.value_as_string, 
				location_uri=amazon_reviews_bucket.s3_url_for_object(),
			)
		)

		amazon_reviews_table = glue.CfnTable(self, "GlueTableAmazonReviews", 
			catalog_id = cfn_glue_db.catalog_id,
			database_name = glue_db_name.value_as_string,
			table_input = glue.CfnTable.TableInputProperty(
				description = "Amazon Customer Reviews (a.k.a. Product Reviews)",
				name = glue_table_name.value_as_string,
				parameters = {
					"classification": "parquet",
					"typeOfData": "file"
				},
				partition_keys = [{"name": "product_category","type": "string"}],
				storage_descriptor = glue.CfnTable.StorageDescriptorProperty(
					columns = [
						{"name": "marketplace", "type": "string"},
						{"name": "customer_id", "type": "string"},
						{"name": "review_id","type": "string"},
						{"name": "product_id","type": "string"},
						{"name": "product_parent","type": "string"},
						{"name": "product_title","type": "string"},
						{"name": "star_rating","type": "int"},
						{"name": "helpful_votes","type": "int"},
						{"name": "total_votes","type": "int"},
						{"name": "vine","type": "string"},
						{"name": "verified_purchase","type": "string"},
						{"name": "review_headline","type": "string"},
						{"name": "review_body","type": "string"},
						{"name": "review_date","type": "bigint"},
						{"name": "year","type": "int"}],
					location = amazon_reviews_bucket.s3_url_for_object() + "/parquet/",
					input_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
					output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
					serde_info = glue.CfnTable.SerdeInfoProperty( 
						serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
						parameters = {
							"classification": "parquet",
							"typeOfData": "file"
						}
					)
				),
				table_type = "EXTERNAL_TABLE"
			)
		)

		# amazon_reviews_table.node.add_dependency(glue_default_permissions)
		amazon_reviews_table.node.add_dependency(cfn_glue_db)

		partition_list = ["Apparel", "Automotive", "Baby", "Beauty", "Books", "Camera", "Digital_Ebook_Purchase", 
			"Digital_Music_Purchase", "Digital_Software", "Digital_Video_Download","Digital_Video_Games", "Electronics",
			"Furniture", "Gift_Card", "Grocery", "Health_&_Personal_Care", "Home", "Home_Entertainment", 
			"Home_Improvement", "Jewelry", "Kitchen", "Lawn_and_Garden", "Luggage", "Major_Appliances", "Mobile_Apps",
			"Mobile_Electronics", "Music", "Musical_Instruments", "Office_Products", "Outdoors", "PC", "Personal_Care_Appliances",
			"Pet_Products", "Shoes", "Software", "Sports", "Tools", "Toys", "Video", "Video_DVD", "Video_Games", 
			"Watches", "Wireless"]

		partition_uri_prefix = f"{amazon_reviews_bucket.s3_url_for_object()}/parquet/{amazon_reviews_table.table_input.partition_keys[0].name}"

		for partition in partition_list:

			cfn_partition_location = partition_uri_prefix + "=" + partition

			cfn_partition_id = "Partition"+partition

			cfn_partition = glue.CfnPartition(self, cfn_partition_id, 
				catalog_id = amazon_reviews_table.catalog_id, 
				database_name = glue_db_name.value_as_string,
				partition_input = glue.CfnPartition.PartitionInputProperty(
					values = [ partition ],
					storage_descriptor = glue.CfnPartition.StorageDescriptorProperty(
						location = cfn_partition_location,
						input_format = "org.apache.hadoop.mapred.TextInputFormat",
						serde_info = glue.CfnPartition.SerdeInfoProperty(
							serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
							parameters = {
								"serialization.format": "1"
							}
						)
					)
				),
				table_name = glue_table_name.value_as_string
			)

			cfn_partition.add_depends_on(amazon_reviews_table)
