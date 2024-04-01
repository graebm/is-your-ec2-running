from dataclasses import dataclass, field

from aws_cdk import (
    Duration,
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions
)
from constructs import Construct


@dataclass
class Settings:
    account: str
    region: str
    schedule: list[str]
    check_regions: list[str]
    check_names: list[str] = field(default_factory=lambda: ['*'])
    ignore_names: list[str] = field(default_factory=list)
    check_types: list[str] = field(default_factory=lambda: ['*'])
    ignore_types: list[str] = field(default_factory=list)
    alert_emails: list[str] = field(default_factory=list)

    def validate(self):
        assert len(self.schedule) > 0
        assert len(self.check_regions) > 0
        assert len(self.check_names) > 0
        assert len(self.check_types) > 0


class IsYourEC2RunningStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 settings: Settings,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an SNS topic
        topic = sns.Topic(
            self, "AlertTopic",
            display_name="Your EC2 Is Running",
        )

        # If user provided emails in settings, subscribe them to the topic
        for email in settings.alert_emails:
            topic.add_subscription(sns_subscriptions.EmailSubscription(email))

        # Create a Lambda function
        lambda_function = aws_lambda.Function(
            self, "Lambda",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("lambda_function"),
            environment={
                'TOPIC_ARN': topic.topic_arn,
                'CHECK_REGIONS': ','.join(settings.check_regions),
                'CHECK_NAMES': ','.join(settings.check_names),
                'IGNORE_NAMES': ','.join(settings.ignore_names),
                'CHECK_TYPES': ','.join(settings.check_types),
                'IGNORE_TYPES': ','.join(settings.ignore_types),
            },
            timeout=Duration.minutes(5),
        )

        # Grant the Lambda function permissions to publish to the SNS topic
        topic.grant_publish(lambda_function)

        # Grant the Lambda function permissions to describe EC2 instances
        lambda_function.add_to_role_policy(iam.PolicyStatement(
            actions=["ec2:DescribeInstances"],
            resources=["*"]
        ))

        # Schedule the Lambda function using CloudWatch Events
        for i, expression in enumerate(settings.schedule):
            rule = events.Rule(
                self, f"RunChecksEvent{i+1}",
                schedule=events.Schedule.expression(expression)
            )
            rule.add_target(targets.LambdaFunction(lambda_function))
