#!/usr/bin/env python3
"""Preflight checks for the Level 1 Bedrock starter."""

from __future__ import annotations

import os
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, NoRegionError


DEFAULT_BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
INFERENCE_PROFILE_PREFIXES = ("us.", "eu.", "apac.", "global.")


def configured_region() -> str | None:
    return os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")


def is_inference_profile(identifier: str) -> bool:
    return identifier.startswith(INFERENCE_PROFILE_PREFIXES)


def verify_default_identifier(bedrock, default_identifier: str, model_ids: list[str]) -> bool:
    if is_inference_profile(default_identifier):
        try:
            profile = bedrock.get_inference_profile(inferenceProfileIdentifier=default_identifier)
        except AttributeError:
            print("Error: this boto3/botocore version cannot check inference profiles. Upgrade boto3.")
            return False
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "Unknown")
            print(
                f"Error: could not confirm inference profile {default_identifier} ({code}). "
                "Make sure the profile is allowed in the configured region/account."
            )
            return False

        print(f"Inference profile confirmed: {profile.get('inferenceProfileName', default_identifier)}")
        routed_models = profile.get("models", [])
        if routed_models:
            print("Profile can route to:")
            for model in routed_models:
                model_arn = model.get("modelArn")
                if model_arn:
                    print(f"  - {model_arn}")
        return True

    if default_identifier not in model_ids:
        print(
            "Error: the configured default model was not found in this region. "
            "Set BEDROCK_MODEL_ID to an available Anthropic model or inference profile."
        )
        return False

    return True


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"boto3: {boto3.__version__}")

    try:
        session = boto3.Session(region_name=configured_region())
        print(f"AWS region: {session.region_name or 'not configured'}")
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        print(f"AWS account: {identity['Account']}")
        print(f"AWS ARN: {identity['Arn']}")

        bedrock = session.client("bedrock")
        response = bedrock.list_foundation_models(byProvider="Anthropic")
        summaries = response.get("modelSummaries", [])
        model_ids = sorted(item["modelId"] for item in summaries if "modelId" in item)

        default_model = os.getenv("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID)
        print(f"Configured Bedrock model/profile ID: {default_model}")
        print("Available Anthropic model IDs:")
        for model_id in model_ids:
            print(f"  - {model_id}")

        if not verify_default_identifier(bedrock, default_model, model_ids):
            return 1
    except NoRegionError:
        print(
            "Error: no AWS region configured. Set AWS_REGION or AWS_DEFAULT_REGION "
            "before running the starter."
        )
        return 1
    except NoCredentialsError:
        print("Error: no AWS credentials found. Authenticate to the VR Labs account first.")
        return 1
    except (ClientError, BotoCoreError) as exc:
        print(f"Error: AWS preflight failed: {exc}")
        return 1

    print("Preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
