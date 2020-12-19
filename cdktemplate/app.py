#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import core
import os

os.environ["AMAZON_REVIEWS_BUCKET_ARN"] = "arn:aws:s3:::amazon-reviews-pds"
os.environ["ROLE_NAME_PREFIX"] = "SageMakerStudioExecutionRole_"

os.environ["NESTED_STACK_URL_PREFIX"] = "https://sagemaker-studio-audit-control.s3.amazonaws.com/"

from sagemaker_studio_audit_control.sagemaker_studio_audit_control_stack import SageMakerStudioAuditControlStack
from sagemaker_studio_audit_control.amazon_reviews_dataset_stack  import AmazonReviewsDatasetStack
from sagemaker_studio_audit_control.data_scientist_users_stack import DataScientistUsersStack
from sagemaker_studio_audit_control.sagemaker_studio_stack import SageMakerStudioStack

app = core.App()
SageMakerStudioAuditControlStack(app, "sagemaker-studio-audit-control")
AmazonReviewsDatasetStack(app, "amazon-reviews-dataset-stack")
DataScientistUsersStack(app, "data-scientist-users-stack")
SageMakerStudioStack(app, "sagemaker-studio-stack")

app.synth()