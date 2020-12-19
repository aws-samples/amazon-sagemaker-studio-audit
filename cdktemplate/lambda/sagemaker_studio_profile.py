# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import cfnresponse
import boto3
import time
from botocore.exceptions import ClientError

client = boto3.client("sagemaker")

SLEEP_INTERVAL = 5
TIMEOUT_OFFSET = SLEEP_INTERVAL + 1

def handler(event, context):

	print("Received event: %s" % event)
	request_type = event["RequestType"]
	if request_type == "Create": return create_resource(event, context)
	elif request_type == "Update": return update_resource(event, context)
	elif request_type == "Delete": return delete_resource(event, context)
	else :
		# Unknown RequestType
		print("Invalid request type: %s." % request_type)
		cfnresponse.send(event, context, cfnresponse.FAILED, {})

def create_resource(event, context):
	try:
		user_profile = client.create_user_profile(
			DomainId = event["ResourceProperties"]["DomainId"],
			UserProfileName = event["ResourceProperties"]["UserProfileName"],
			UserSettings={
				"ExecutionRole": event["ResourceProperties"]["ExecutionRole"]
			}
		)
		response_data = { "UserProfileArn" : user_profile["UserProfileArn"]}
		cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)

	except ClientError as e:
		print("Unexpected error: %s" % e)
		cfnresponse.send(event, context, cfnresponse.FAILED, {})

def update_resource(event, context):
	try:
		user_profile = client.update_user_profile(
			DomainId = event["ResourceProperties"]["DomainId"],
			UserProfileName = event["ResourceProperties"]["UserProfileName"],
			UserSettings={
				"ExecutionRole": event["ResourceProperties"]["ExecutionRole"]
			}
		)
		response_data = { "UserProfileArn" : user_profile["UserProfileArn"]}
		cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
		
	except ClientError as e:
		if e.response['Error']['Code'] == 'ResourceNotFound':
			print("Resource not found. Creating resource.")
			return create_user_profile(event, context)
		else:
			print("Unexpected error: %s." % e)
			cfnresponse.send(event, context, cfnresponse.FAILED, {})

def delete_resource(event, context):

	domain_id = event["ResourceProperties"]["DomainId"]
	user_profile_name = event["ResourceProperties"]["UserProfileName"]
	response_data = { "UserProfileName" : user_profile_name }

	try:
		print("Received delete event.")

		delete_response = client.delete_user_profile(
			DomainId = domain_id,
			UserProfileName = user_profile_name
		)

		print("Checking Delete status.")
		user_profile_status = client.describe_user_profile( DomainId = domain_id, UserProfileName = user_profile_name)["Status"]

		while True:
			if context.get_remaining_time_in_millis() < TIMEOUT_OFFSET:
				print("Lambda Function about to time out. Aborting.")
				cfnresponse.send(event, context, cfnresponse.FAILED, response_data)

			if user_profile_status in ["Deleting", "Pending", "InService"] :
				print("Waiting for Deletion.")
				time.sleep(SLEEP_INTERVAL)
				user_profile_status = client.describe_user_profile( DomainId = domain_id, UserProfileName = user_profile_name)["Status"]
			else: #domain_status == "Failed"
				print("Delete User Profile Failed.")
				cfnresponse.send(event, context, cfnresponse.FAILED, response_data)

	except ClientError as e:

		if e.response['Error']['Code'] == 'ResourceNotFound':
			print("User Profile successfully deleted.")
			cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data)
		else:
			print("Unexpected error: %s" % e)
			cfnresponse.send(event, context, cfnresponse.FAILED, response_data)
