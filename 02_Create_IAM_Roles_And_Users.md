## Creating required IAM roles and users for data scientists

To demonstrate how you can provide differentiated access to the dataset registered in the previous step, you first need to create IAM policies, roles, a group, and users. The following diagram illustrates the resources you configure in this section.

<p align="center">
    <img src="./images/7IAMUsersAndGroups.png" />
</p>

In this section, you complete the following high-level steps:

1. Create an IAM group named `DataScientists` containing two users: `data-scientist-full` and `data-scientist-limited`, to control their access to the console and to Studio.
2. Create a managed policy named `DataScientistGroupPolicy` and assign it to the group.

The policy allows users in the group to access Studio, but only using a SageMaker user profile that matches their IAM user name. It also denies the use of SageMaker notebook instances, allowing Studio notebooks only.

3. For each IAM user, create individual IAM roles, which are used as user profile execution roles in Studio later.

The naming convention for these roles consists of a common prefix followed by the corresponding IAM user name. This allows you to audit activities on Studio notebooks—which are logged using Studio’s execution roles—and trace them back to the individual IAM users who performed the activities. For this post, I use the prefix `SageMakerStudioExecutionRole_`.

4. Create a managed policy named `SageMakerUserProfileExecutionPolicy` and assign it to each of the IAM roles.

The policy establishes coarse-grained access permissions to the data lake.

Follow the remainder of this section to create the IAM resources described. The permissions configured in this section grant common, coarse-grained access to data lake resources for all the IAM roles. In a later section, you use Lake Formation to establish fine-grained access permissions to Data Catalog resources and Amazon S3 locations for individual roles.

### Creating the required IAM group and users:

To create your group and users, complete the following steps:

1. Sign in to the console using an IAM user with permissions to create groups, users, roles, and policies.
2. On the IAM console, [create policies on the JSON tab](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html#access_policies_create-json-editor) to create a new IAM managed policy named `DataScientistGroupPolicy`.
    - Use the following JSON policy document to provide permissions, providing your AWS Region and AWS account ID:

        <pre class=" language-json">
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "sagemaker:DescribeDomain",
                        "sagemaker:ListDomains",
                        "sagemaker:ListUserProfiles",
                        "sagemaker:ListApps"
                    ],
                    "Resource": "*",
                    "Effect": "Allow"
                },
                {
                    "Action": [
                        "sagemaker:CreatePresignedDomainUrl",
                        "sagemaker:DescribeUserProfile"
                    ],
                    "Resource": "arn:aws:sagemaker:<span style="color: #ff0000"><em>&lt;AWSREGION&gt;</em></span>:<span style="color: #ff0000"><em>&lt;AWSACCOUNT&gt;</em></span>:user-profile/*/${aws:username}",
                    "Effect": "Allow"
                },
                {
                    "Action": [
                        "sagemaker:CreatePresignedDomainUrl",
                        "sagemaker:DescribeUserProfile"
                    ],
                    "Effect": "Deny",
                    "NotResource": "arn:aws:sagemaker:<span style="color: #ff0000"><em>&lt;AWSREGION&gt;</em></span>:<span style="color: #ff0000"><em>&lt;AWSACCOUNT&gt;</em></span>:user-profile/*/${aws:username}"
                },
                {
                    "Action": "sagemaker:*App",
                    "Resource": "arn:aws:sagemaker:<span style="color: #ff0000"><em>&lt;AWSREGION&gt;</em></span>:<span style="color: #ff0000"><em>&lt;AWSACCOUNT&gt;</em></span>:app/*/${aws:username}/*",
                    "Effect": "Allow"
                },
                {
                    "Action": "sagemaker:*App",
                    "Effect": "Deny",
                    "NotResource": "arn:aws:sagemaker:<span style="color: #ff0000"><em>&lt;AWSREGION&gt;</em></span>:<span style="color: #ff0000"><em>&lt;AWSACCOUNT&gt;</em></span>:app/*/${aws:username}/*"
                },
                {
                    "Action": [
                        "sagemaker:CreatePresignedNotebookInstanceUrl",
                        "sagemaker:*NotebookInstance",
                        "sagemaker:*NotebookInstanceLifecycleConfig",
                        "sagemaker:CreateUserProfile",
                        "sagemaker:DeleteDomain",
                        "sagemaker:DeleteUserProfile"
                    ],
                    "Resource": "*",
                    "Effect": "Deny"
                }
            ]
        }
        </pre>

This policy forces an IAM user to open Studio using a SageMaker user profile with the same name. It also denies the use of SageMaker notebook instances, allowing Studio notebooks only.

1. [Create an IAM group](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_groups_create.html).
    - For **Group name**, enter `DataScientists`.
    - Search and attach the AWS managed policy named `DataScientist` and the IAM policy created in the previous step.

2. [Create two IAM users](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console) named `data-scientist-full` and `data-scientist-limited`.

Alternatively, you can provide names of your choice, as long as they’re a combination of lowercase letters, numbers, and hyphen (-). Later, you also give these names to their corresponding SageMaker user profiles, which at the time of writing [only support those characters](https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateUserProfile.html#sagemaker-CreateUserProfile-request-UserProfileName).

### Creating the required IAM roles:

To create your roles, complete the following steps:

1. On the IAM console, [create a new managed policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create-console.html#access_policies_create-json-editor) named `SageMakerUserProfileExecutionPolicy`. 
    - Use the following policy code:

        <pre class=" language-json">
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "lakeformation:GetDataAccess",
                        "glue:GetTable",
                        "glue:GetTables",
                        "glue:SearchTables",
                        "glue:GetDatabase",
                        "glue:GetDatabases",
                        "glue:GetPartitions"
                    ],
                    "Resource": "*",
                    "Effect": "Allow"
                },
                {
                    "Action": "sts:AssumeRole",
                    "Resource": "*",
                    "Effect": "Deny"
                }
            ]
        }
        </pre>

This policy provides common coarse-grained IAM permissions to the data lake, leaving Lake Formation permissions to control access to Data Catalog resources and Amazon S3 locations for individual users and roles. This is the recommended method for granting access to data in Lake Formation. For more information, see [Methods for Fine-Grained Access Control](https://docs.aws.amazon.com/lake-formation/latest/dg/access-control-fine-grained.html).

2. [Create an IAM role](https://docs.aws.amazon.com/glue/latest/dg/create-an-iam-role-sagemaker-notebook.html) for the first data scientist (`data-scientist-full`), which is used as the corresponding user profile’s execution role. 
    - On the **Attach permissions policy** page, search and attach the AWS managed policy `AmazonSageMakerFullAccess`.
    - For **Role name**, use the naming convention introduced at the beginning of this section to name the role `SageMakerStudioExecutionRole_data-scientist-full`.

3. To add the remaining policies, on the **Roles** page, choose the role name you just created. 
4. Under **Permissions** , choose **Attach policies**
5. Search and select the `SageMakerUserProfileExecutionPolicy` and `AmazonAthenaFullAccess` policies
6. Choose **Attach policy**.
7. To restrict the Studio resources that can be created within Studio (such as image, kernel, or instance type) to only those belonging to the user profile associated to the first IAM role, [embed an inline policy to the IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html#embed-inline-policy-console).
    - Use the following JSON policy document to scope down permissions for the user profile, providing the Region, account ID, and IAM user name associated to the first data scientist (`data-scientist-full`). You can name the inline policy `DataScientist1IAMRoleInlinePolicy`. 


        <pre class=" language-json">
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sagemaker:*App",
                    "Resource": "arn:aws:sagemaker:<span style="color: #ff0000"><em>&lt;AWSREGION&gt;</em></span>:<span style="color: #ff0000"><em>&lt;AWSACCOUNT&gt;</em></span>:app/*/<span style="color: #ff0000"><em>&lt;IAMUSERNAME&gt;</em></span>/*",
                    "Effect": "Allow"
                },
                {
                    "Action": "sagemaker:*App",
                    "Effect": "Deny",
                    "NotResource": "arn:aws:sagemaker:<span style="color: #ff0000"><em>&lt;AWSREGION&gt;</em></span>:<span style="color: #ff0000"><em>&lt;AWSACCOUNT&gt;</em></span>:app/*/<span style="color: #ff0000"><em>&lt;IAMUSERNAME&gt;</em></span>/*"
                }
            ]
        }
        </pre>

8. Repeat the previous steps to create an IAM role for the second data scientist (`data-scientist-limited`). 
   - Name the role `SageMakerStudioExecutionRole_data-scientist-limited` and the second inline policy `DataScientist2IAMRoleInlinePolicy`.

## [Proceed to the next section](./03_Grant_Permissions_With_Lake_Formation.md) to grant data permissions with Lake Formation.

