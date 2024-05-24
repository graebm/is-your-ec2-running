import boto3
from boto3.session import Session
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
from fnmatch import fnmatch
import os


class Checker:
    def __init__(self):
        self.check_names = os.environ['CHECK_NAMES'].lower().split(',')
        self.ignore_names = os.environ['IGNORE_NAMES'].lower().split(',')
        self.check_types = os.environ['CHECK_TYPES'].lower().split(',')
        self.ignore_types = os.environ['IGNORE_TYPES'].lower().split(',')

    def _should_alert(self, instance_name, instance_type):
        instance_name = instance_name.lower()
        instance_type = instance_type.lower()
        if not any(fnmatch(instance_name, pattern) for pattern in self.check_names):
            return False
        if any(fnmatch(instance_name, pattern) for pattern in self.ignore_names):
            return False
        if not any(fnmatch(instance_type, pattern) for pattern in self.check_types):
            return False
        if any(fnmatch(instance_type, pattern) for pattern in self.ignore_types):
            return False
        return True

    def get_running_instances(self, region) -> list[str]:
        """Check for running EC2 instances in this region.
        Returns a list of strings, with an entry about each running instance"""
        messages = []
        try:
            ec2 = boto3.client('ec2', region_name=region)
            paginator = ec2.get_paginator('describe_instances')
            page_iterator = paginator.paginate(Filters=[{
                'Name': 'instance-state-name',
                'Values': ['running']
            }])

            for page in page_iterator:
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        instance_type = instance['InstanceType']
                        instance_name = '<none>'
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                instance_name = tag['Value']
                        line = (f"name: {instance_name}, type: {instance_type}, "
                                f"region: {region}, id: {instance_id}")
                        if self._should_alert(instance_name, instance_type):
                            messages.append(line)

        except ClientError as e:
            # AuthFailure happens if a region isn't enabled for your account,
            # so you definitely didn't leave something running there
            if e.response['Error']['Code'] == 'AuthFailure':
                pass
            else:
                raise

        return messages


def lambda_handler(event, context):
    sns = boto3.client('sns')
    messages = []

    checker = Checker()

    # check each region in parallel
    regions = os.environ['CHECK_REGIONS'].split(',')
    with ThreadPoolExecutor() as executor:
        for region_messages in executor.map(checker.get_running_instances, regions):
            messages.extend(region_messages)

    if messages:
        count = len(messages)
        instance_s = "instance" if count == 1 else "instances"
        subject = f"Alert: {count} running EC2 {instance_s}"
        final_message = "These are running:"
        for i, line in enumerate(messages):
            final_message += f"\n{i + 1}) {line}"
        print(subject)
        print(final_message)
        sns.publish(
            TopicArn=os.environ['TOPIC_ARN'],
            Message=final_message,
            Subject=subject
        )
        response_body = f"{subject}\n{final_message}"
    else:
        response_body = "No running instances"

    return {
        'statusCode': 200,
        'body': response_body,
    }


if __name__ == '__main__':
    print(lambda_handler(None, None))
