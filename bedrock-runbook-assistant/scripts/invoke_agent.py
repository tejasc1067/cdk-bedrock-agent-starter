#!/usr/bin/env python3
"""Invoke an existing Bedrock agent alias from Python."""

from __future__ import annotations

import argparse
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, NoRegionError


def configured_region() -> str | None:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-id", required=True, help="Bedrock agent ID.")
    parser.add_argument("--agent-alias-id", required=True, help="Bedrock agent alias ID.")
    parser.add_argument("--prompt", required=True, help="Input text for the agent.")
    parser.add_argument(
        "--session-id",
        default="level1-session",
        help="Session ID used by Bedrock agent runtime. Defaults to level1-session.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        session = boto3.Session(region_name=configured_region())
        client = session.client("bedrock-agent-runtime")
        response = client.invoke_agent(
            agentId=args.agent_id,
            agentAliasId=args.agent_alias_id,
            sessionId=args.session_id,
            inputText=args.prompt,
        )

        parts: list[str] = []
        for event in response["completion"]:
            chunk = event.get("chunk")
            if chunk and "bytes" in chunk:
                parts.append(chunk["bytes"].decode("utf-8"))

        print("".join(parts).strip())
        return 0
    except NoRegionError:
        print("Error: no AWS region configured. Set AWS_REGION or AWS_DEFAULT_REGION.")
        return 1
    except NoCredentialsError:
        print("Error: no AWS credentials found.")
        return 1
    except (ClientError, BotoCoreError) as exc:
        print(f"Error: agent invocation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
