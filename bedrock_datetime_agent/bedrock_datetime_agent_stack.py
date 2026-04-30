import json
from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class BedrockDateTimeAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = self.node.try_get_context("prefix") or "datetime"
        tz_name = self.node.try_get_context("timezone_name") or "IST"
        tz_hours = int(self.node.try_get_context("timezone_offset_hours") or 5)
        tz_minutes = int(self.node.try_get_context("timezone_offset_minutes") or 30)
        foundation_model = self.node.try_get_context("foundation_model") or "us.anthropic.claude-sonnet-4-6"
        idle_session_ttl = int(self.node.try_get_context("idle_session_ttl") or 600)
        lambda_timeout = int(self.node.try_get_context("lambda_timeout") or 10)

        sign = "+" if tz_hours >= 0 else ""
        tz_offset_str = f"UTC{sign}{tz_hours}:{abs(tz_minutes):02d}"

        datetime_fn = _lambda.Function(
            self, "DateTimeFn",
            function_name=f"{prefix}-datetime-fn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(lambda_timeout),
            environment={
                "TZ_NAME": tz_name,
                "TZ_OFFSET_HOURS": str(tz_hours),
                "TZ_OFFSET_MINUTES": str(tz_minutes),
            },
        )

        agent_role = iam.Role(
            self, "BedrockAgentRole",
            role_name=f"{prefix}-bedrock-agent-role",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description=f"Allows Bedrock agent ({prefix}) to invoke foundation models",
        )

        agent_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:GetInferenceProfile",
            ],
            resources=[
                "arn:aws:bedrock:*::foundation-model/*",
                f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/*",
            ],
        ))

        datetime_fn.add_permission(
            "AllowBedrock",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
        )

        schema_path = Path(__file__).parent.parent / "schema" / "action_group_schema.json"
        with open(schema_path) as f:
            schema_str = json.dumps(json.load(f))

        agent = bedrock.CfnAgent(
            self, "DateTimeAgent",
            agent_name=f"{prefix}-datetime-agent",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model=foundation_model,
            instruction=(
                f"You are a strictly scoped assistant. Your only job is to tell users "
                f"the current date, time, day of the week, or any combination of these "
                f"in {tz_name} ({tz_offset_str}). "
                f"When asked about date, time, day, or datetime in {tz_name}, "
                f"always call the getDateTime action and return the result. "
                "Do not guess, hardcode, or infer the time — always fetch it. "
                "If a user asks anything that is not related to the current date or time "
                "— including general knowledge, coding, math, opinions, weather, "
                "or any other topic — respond only with: "
                f"'I can only tell you the current date and time in {tz_name}. "
                "Please ask me about that.' "
                "Do not make exceptions. Do not engage with off-topic requests in any way."
            ),
            idle_session_ttl_in_seconds=idle_session_ttl,
            auto_prepare=True,
            skip_resource_in_use_check_on_delete=True,
            action_groups=[
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name=f"{prefix}-datetime-action-group",
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=datetime_fn.function_arn,
                    ),
                    api_schema=bedrock.CfnAgent.APISchemaProperty(
                        payload=schema_str,
                    ),
                    action_group_state="ENABLED",
                )
            ],
        )

        alias = bedrock.CfnAgentAlias(
            self, "DateTimeAgentAlias",
            agent_id=agent.attr_agent_id,
            agent_alias_name="live",
        )

        p = prefix.capitalize()
        CfnOutput(self, "AgentId", value=agent.attr_agent_id, export_name=f"{p}AgentId")
        CfnOutput(self, "AliasId", value=alias.attr_agent_alias_id, export_name=f"{p}AliasId")
        CfnOutput(self, "LambdaArn", value=datetime_fn.function_arn, export_name=f"{p}LambdaArn")
        CfnOutput(self, "AgentRoleArn", value=agent_role.role_arn, export_name=f"{p}AgentRoleArn")
