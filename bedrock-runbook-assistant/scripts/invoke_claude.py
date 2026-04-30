#!/usr/bin/env python3
"""Make a direct Bedrock Claude call with the Messages API."""

from __future__ import annotations

import argparse
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, NoRegionError


DEFAULT_BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"


def configured_region() -> str | None:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="User prompt to send to Bedrock.")
    parser.add_argument(
        "--model-id",
        default=os.getenv("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID),
        help=(
            "Bedrock model or inference profile ID. Defaults to BEDROCK_MODEL_ID "
            f"or {DEFAULT_BEDROCK_MODEL_ID}."
        ),
    )
    parser.add_argument("--system", help="Optional system prompt.")
    return parser.parse_args()


def extract_text(response: dict) -> str:
    content = response.get("output", {}).get("message", {}).get("content", [])
    parts: list[str] = []
    for block in content:
        text = block.get("text")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def main() -> int:
    args = parse_args()
    try:
        session = boto3.Session(region_name=configured_region())
        client = session.client("bedrock-runtime")
        request = {
            "modelId": args.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": args.prompt}],
                }
            ],
        }
        if args.system:
            request["system"] = [{"text": args.system}]

        response = client.converse(**request)
        print(extract_text(response))
        return 0
    except NoRegionError:
        print("Error: no AWS region configured. Set AWS_REGION or AWS_DEFAULT_REGION.")
        return 1
    except NoCredentialsError:
        print("Error: no AWS credentials found.")
        return 1
    except (ClientError, BotoCoreError) as exc:
        print(f"Error: model invocation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
