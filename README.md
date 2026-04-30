# Bedrock DateTime Agent

A generic AWS Bedrock agent that returns the current date and time in any configurable timezone. Built with AWS CDK (Python). Designed so multiple people can deploy their own independent stacks from the same codebase.

## What it does

- Responds **only** to questions about the current date, time, or day in the configured timezone
- Calls a Lambda function to fetch the live time — never guesses or hardcodes it
- Rejects all off-topic questions with a fixed message

## Stack

| Resource | Default | Configurable |
|---|---|---|
| Foundation model | `us.anthropic.claude-sonnet-4-6` | Yes |
| Lambda runtime | Python 3.12 | No |
| Action group | OpenAPI 3.0 — `GET /get-datetime` | No |
| Timezone | IST (UTC+5:30) | Yes |

## Project structure

```
.
├── app.py                                      # CDK entry point
├── cdk.json                                    # Default context values
├── requirements.txt
├── bedrock_datetime_agent/
│   └── bedrock_datetime_agent_stack.py         # All infrastructure
├── lambda/
│   └── lambda_function.py                      # Timezone-aware time handler
└── schema/
    └── action_group_schema.json                # OpenAPI schema (inlined at deploy)
```

## Configuration

All deployment parameters are controlled via CDK context. Defaults live in `cdk.json`:

```json
{
  "context": {
    "prefix": "myteam",
    "timezone_name": "IST",
    "timezone_offset_hours": 5,
    "timezone_offset_minutes": 30,
    "foundation_model": "us.anthropic.claude-sonnet-4-6",
    "idle_session_ttl": 600,
    "lambda_timeout": 10
  }
}
```

The `prefix` value is used to name every AWS resource (`alice-datetime-fn`, `alice-bedrock-agent-role`, etc.), so multiple people can deploy into the same account without conflicts.

## Prerequisites

- AWS CLI configured with valid credentials
- Python 3.10+
- Node.js (required by CDK CLI)
- CDK CLI: `npm install -g aws-cdk`
- Model access enabled for `Claude Sonnet 4` in [Amazon Bedrock console](https://console.aws.amazon.com/bedrock) → Model access

## Setup

```bash
pip install -r requirements.txt

# One-time per account/region
cdk bootstrap
```

## Deploy

**Option A — edit `cdk.json` then deploy:**

```bash
# Set your prefix and timezone in cdk.json, then:
cdk deploy
```

**Option B — pass context flags at deploy time (no file edits):**

```bash
# IST example
cdk deploy --context prefix=alice --context timezone_name=IST --context timezone_offset_hours=5 --context timezone_offset_minutes=30

# EST example
cdk deploy --context prefix=bob --context timezone_name=EST --context timezone_offset_hours=-5 --context timezone_offset_minutes=0
```

Stack outputs after deploy (names are prefix-based):

```
AliceDateTimeAgentStack.AgentId     = <agent-id>
AliceDateTimeAgentStack.AliasId     = <alias-id>
AliceDateTimeAgentStack.LambdaArn   = arn:aws:lambda:...
AliceDateTimeAgentStack.AgentRoleArn = arn:aws:iam:...
```

## Invoke the agent

The `bedrock-runbook-assistant/` folder contains ready-to-use CLI scripts for both agent invocation and direct Claude calls.

### Setup (one-time)

```bash
cd bedrock-runbook-assistant
python -m venv .venv

# Mac/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
export AWS_REGION=us-east-1
```

Verify your environment is ready:

```bash
python scripts/check_env.py
```

### Invoke the datetime agent

Use the `AgentId` and `AliasId` from the CDK deploy outputs:

```bash
python scripts/invoke_agent.py \
  --agent-id <AgentId from CDK output> \
  --agent-alias-id <AliasId from CDK output> \
  --prompt "What is the current time?"
```

Optional `--session-id` flag to maintain conversation context across calls (defaults to `level1-session`).

### Call Claude directly (no agent)

Hits the Bedrock Converse API directly — useful for testing prompts without going through the agent layer:

```bash
python scripts/invoke_claude.py --prompt "What is Amazon Bedrock in one sentence?"

# With a system prompt or custom model
python scripts/invoke_claude.py \
  --model-id us.anthropic.claude-sonnet-4-6 \
  --system "You are a concise technical assistant." \
  --prompt "Explain Bedrock inference profiles in one sentence."
```

Default model is `us.anthropic.claude-sonnet-4-6`. Override via `--model-id` or the `BEDROCK_MODEL_ID` env var.

### Python (inline)

```python
import boto3

client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

response = client.invoke_agent(
    agentId="<AgentId from CDK output>",
    agentAliasId="<AliasId from CDK output>",
    sessionId="session-001",
    inputText="What is the current time?",
)

for event in response["completion"]:
    if "chunk" in event:
        print(event["chunk"]["bytes"].decode())
```

## Teardown

```bash
cdk destroy
```

## Notes

- The Lambda reads timezone from environment variables (`TZ_NAME`, `TZ_OFFSET_HOURS`, `TZ_OFFSET_MINUTES`) set by the CDK stack — no hardcoded offsets
- Uses only Python stdlib — no `pytz` or third-party packages needed in the Lambda
- `auto_prepare=True` on the agent means CloudFormation handles preparation automatically on every deploy
