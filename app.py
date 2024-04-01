#!/usr/bin/env python3
import json

import aws_cdk as cdk

from is_your_ec2_running.is_your_ec2_running_stack import IsYourEC2RunningStack, Settings


def load_settings(app: cdk.App) -> Settings:
    settings_path = app.node.try_get_context("settings")
    if settings_path is None:
        exit('You must pass settings via: -c settings=<path>. ' +
             'See README.md for more details.')

    with open(settings_path) as f:
        settings_json = json.load(f)

    settings = Settings(**settings_json)
    settings.validate()
    return settings


app = cdk.App()
settings = load_settings(app)
IsYourEC2RunningStack(
    app, "IsYourEC2Running",
    description="Stack to check if you left any EC2 instances running",
    env=cdk.Environment(account=settings.account,
                        region=settings.region),
    settings=settings,
)

app.synth()
