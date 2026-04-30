# Bedrock Runbook Assistant Starter

This starter is the default scaffold for the Level 1 lab.

It is intentionally small. The point is to help learners spend time on Bedrock, agent behavior, evaluation, and judgment instead of boilerplate setup.

## Defaults
- AWS account: VR Labs account only
- Coding tool: Claude Code
- Runtime stack: Python 3 + boto3
- Default Bedrock model/profile ID for direct model calls: `us.anthropic.claude-sonnet-4-6`
- Direct model behind the profile: Claude Sonnet 4.6
- Fast-path model for simple tasks: Claude Haiku 4.5

## What Is In This Starter
- `scripts/check_env.py`: verifies Python, boto3, AWS identity, Anthropic model visibility, and the configured Bedrock model/profile ID
- `scripts/invoke_claude.py`: makes a direct Bedrock Claude call with Python
- `scripts/invoke_agent.py`: invokes an existing Bedrock agent alias with Python
- `docs/sample-runbooks/`: place approved training docs here
- `artifacts/`: prompt log, checkpoint, architecture note, safety and cost note, and backlog

## Quickstart
```bash
cd starter/bedrock-runbook-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AWS_PROFILE=vr-labs
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
python scripts/check_env.py
python scripts/invoke_claude.py --prompt "What is Amazon Bedrock in one sentence?"
```

Use the facilitator-provided profile name if your local AWS profile is not named `vr-labs`.

The direct Claude script defaults to the US geo inference profile for Claude Sonnet 4.6. Override it only when the facilitator gives you a different approved Bedrock profile:

```bash
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6 python scripts/invoke_claude.py --prompt "What is Amazon Bedrock in one sentence?"
```

## Agent Invocation Example
Once you have created an agent and alias in the VR Labs account:

```bash
python scripts/invoke_agent.py \
  --agent-id YOUR_AGENT_ID \
  --agent-alias-id YOUR_ALIAS_ID \
  --prompt "Summarize the restart steps for service X."
```

## Rules
- Keep the lab narrow.
- Prefer code paths over console clicks whenever a reasonable code path exists.
- Use only approved training documents.
- Do not paste secrets or client-sensitive material into the repo, prompts, or scripts.
- Do not turn this into a production platform build.

## Suggested Next Step
Use this starter for the first successful Bedrock call and the first successful Bedrock agent invocation, then adapt it to the runbook lab use case.
