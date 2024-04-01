
# Is Your EC2 Running?

If you worry about accidentally leaving an expensive EC2 instance running, this project is here to help.

This project is a CDK stack. Deploy it to your account to regularly check for any running EC2 instances, and get emails if there are.

You can customize when it checks, and the names and EC2 types it checks for (by default it alerts you about any that are running).

# Customize

You must create a settings file in this folder. Name it like "myname.settings.json". It should look like:
```json
{
    "account": "012345678901",
    "region": "us-west-2",
    "alert_emails": ["myname@gmail.com", "myname@amazon.com"],
    "schedule": ["cron(0 3 * * ? *)", "cron(0 11 * * ? *)"],
    "check_regions": ["us-west-2", "us-east-1", "us-east-2", "eu-west-1"],
    "check_names": ["*"],
    "ignore_names": [],
    "check_types": ["*"],
    "ignore_types": []
}
```
Fields are:
* `account`: AWS account ID
* `region`: AWS region where this CDK stack will be deployed.
* `alert_emails`: List of email addresses that will receive notifications, via AWS SNS.
* `schedule`: List of schedule [expressions using rate or cron](https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html). These control when the checks occur. In this example, they run twice a day. At 7PM PST (03:00 UTC) when I'm done with work for the day, and 3AM PST (11:00 UTC) in case I was messing around at night I'll see the alert when I wake up.
* `check_regions`: List of AWS regions to check for running EC2 instances.
* `check_names`: List of instance names to check for. By default, this is `["*"]`. But maybe you want something like `["test*"]`.
* `ignore_names`: List of instance names to ignore. By default, this is `[]`.
* `check_types`: List of EC2 instance types to check for. By default, this is `["*"]`. But maybe you want something like `["p5*", "p4*"]`
* `ignore_types`: List of EC2 instance types to ignore. By default, this is `[]`.

# Deploy to your account

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

Deploy this CDK app, passing in your settings file:

```
$ cdk deploy -c settings=myname.settings.json
```

Go to the email addresses you entered, and confirm the subscriptions.

# Testing

To test if this is working, launch and EC2 instance you wouldn't want to leave running overnight. Then go to the AWS Lambda console, and manually invoke "IsYourEC2Running-LambdaXYZXYZ" via the Test tab. You should see in the Lambda's response whether it detected the instance, and if it did you should get an email about it.
