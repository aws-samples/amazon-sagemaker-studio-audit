# CDK template for "Control and audit data exploration activities with Amazon SageMaker Studio and AWS Lake Formation"

This is the CDK template for "Control and audit data exploration activities with Amazon SageMaker Studio and AWS Lake Formation".

Note that the stacks are configured as nested stacks with static URL based on the environment variable `NESTED_STACK_URL_PREFIX`. The parent stack is `sagemaker_studio_audit_control/sagemaker_studio_audit_control_stack.py`

If you are planning to rebuild the CloudFormation template to deploy in your own environment, make sure to edit `app.py` and modify the environment variable `os.environ["NESTED_STACK_URL_PREFIX"]` at the beginning of the file.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initializationprocess also creates a virtualenv within this project, stored under the .env directory.  To create the virtualenv it assumes that there is a `python3` (or `python` for Windows) executable in your path with access to the `venv` package. If for any reason the automatic creation of the virtualenv fails, you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation templates for this code and save each stack as YAML files.

```
$ cdk synth --version-reporting false --path-metadata false

$ cdk synth --version-reporting false --path-metadata false amazon-reviews-dataset-stack > AmazonReviewsDatasetStack.yaml

$ cdk synth --version-reporting false --path-metadata false data-scientist-users-stack > DataScientistUsersStack.yaml

$ cdk synth --version-reporting false --path-metadata false sagemaker-studio-stack > SageMakerStudioStack.yaml

$ cdk synth --version-reporting false --path-metadata false sagemaker-studio-audit-control > SageMakerStudioAuditControlStack.yaml
```

To add additional dependencies, for example other CDK libraries, just addthem to your `setup.py` file and rerun the `pip install -r requirements.txt` command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
