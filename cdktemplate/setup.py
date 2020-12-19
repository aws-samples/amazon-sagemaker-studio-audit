# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="sagemaker_studio_audit_control",
    version="0.0.1",

    description="SageMaker Studio Audit and Control",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Rodrigo Alarcon",

    package_dir={"": "sagemaker_studio_audit_control"},
    packages=setuptools.find_packages(where="sagemaker_studio_audit_control"),

    install_requires=[
        "aws-cdk.core==1.71.0",
        "aws-cdk.aws-iam",
        "aws-cdk.aws_lakeformation",
        "aws-cdk.aws_glue",
        "aws-cdk.aws_s3",
        "aws-cdk.aws_lambda"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
