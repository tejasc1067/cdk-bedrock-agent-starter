#!/usr/bin/env python3
import aws_cdk as cdk
from bedrock_datetime_agent.bedrock_datetime_agent_stack import BedrockDateTimeAgentStack

app = cdk.App()

prefix = app.node.try_get_context("prefix") or "datetime"
BedrockDateTimeAgentStack(app, f"{prefix}DateTimeAgentStack")

app.synth()
