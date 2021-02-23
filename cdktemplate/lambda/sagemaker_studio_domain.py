# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import cfnresponse
import boto3
import time
from botocore.exceptions import ClientError

sm = boto3.client("sagemaker")

SLEEP_INTERVAL = 10
TIMEOUT_OFFSET = SLEEP_INTERVAL + 1

def handler(event, context):
	print("Received event: %s." % event)
	request_type = event["RequestType"]

	if request_type == "Create": return create_resource(event, context)
	elif request_type == "Update": return update_resource(event, context)
	elif request_type == "Delete": return delete_resource(event, context)
	else :
		print("Unknown RequestType: %s." % request_type)
		cfnresponse.send(event, context, cfnresponse.FAILED, {})

def create_resource(event, context):
	try:
		current_timestamp = int(round(time.time() * 1000))
		sm_domain = sm.create_domain(
			DomainName = "default-{}".format(current_timestamp),
			AuthMode = "IAM",
			SubnetIds = event["ResourceProperties"]["SubnetIds"],
			VpcId = event["ResourceProperties"]["VpcId"],
			DefaultUserSettings = {
				"ExecutionRole": event["ResourceProperties"]["DefaultExecutionRole"]
			},
			# AppNetworkAccessType = "VpcOnly",
		)
		domain_id = sm_domain["DomainArn"].split("/")[1]
		domain_status = sm.describe_domain(DomainId = domain_id)["Status"]
		response_data = {"DomainId" : domain_id}

		while domain_status != "InService":

			if context.get_remaining_time_in_millis() < TIMEOUT_OFFSET:
				print("Lambda Function about to time out. Aborting.")
				cfnresponse.send(event, context, cfnresponse.FAILED, response_data)

			if domain_status == "Pending":
				print("Waiting for InService status.")
				time.sleep(SLEEP_INTERVAL)
				domain_status = sm.describe_domain(DomainId = domain_id)["Status"]
			elif domain_status == "Deleting":
				print("Create Domain Failed. Domain being deleted by another process.")
				cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
			else: #domain_status == "Failed" or Unknown
				print("Create Domain Failed. Status: %s" % domain_status)
				cfnresponse.send(event, context, cfnresponse.FAILED, response_data)

		cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)

	except ClientError as e:
		print("Unexpected error: %s." % e)
		cfnresponse.send(event, context, cfnresponse.FAILED, {})

def update_resource(event, context):
	try:
		print("Received Update event.")
		cfnresponse.send(event, context, cfnresponse.SUCCESS, {})

	except ClientError as e:
		print("Unexpected error: %s." % e)
		cfnresponse.send(event, context, cfnresponse.FAILED, {})

def delete_resource(event, context):
	domain_id = ""
	try:
		print("Received Delete event")
		domains = sm.list_domains()["Domains"]

		if len(domains) == 0:
			print("Resource not found. Nothing to do.")
			cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
			return
		else:
			domain_id = domains[0]["DomainId"]
			sm.delete_domain( DomainId = domain_id, RetentionPolicy={ 'HomeEfsFileSystem': 'Delete'} )

		print("Checking Delete status.")
		domain_status = sm.describe_domain(DomainId = domain_id)["Status"]

		while True:
			if context.get_remaining_time_in_millis() < TIMEOUT_OFFSET:
				print("Lambda Function about to time out. Aborting.")
				cfnresponse.send(event, context, cfnresponse.FAILED, {})

			if domain_status in ["Deleting", "Pending", "InService"] :
				print("Waiting for Deletion.")
				time.sleep(SLEEP_INTERVAL)
				domain_status = sm.describe_domain(DomainId = domain_id)["Status"]
			else: # "Failed" or Unknown
				print("Delete Domain Failed. Status: %s" % domain_status)
				cfnresponse.send(event, context, cfnresponse.FAILED, {})

	except ClientError as e:

		if e.response['Error']['Code'] == 'ResourceNotFound':
			print("Domain successfully deleted.")
			cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
		else:
			print("Unexpected error: %s." % e)
			cfnresponse.send(event, context, cfnresponse.FAILED, {})