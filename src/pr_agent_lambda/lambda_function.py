"""AWS Lambda entrypoint for PR agent processing."""

import json
import os
from typing import Dict, Any

# Load .env if it exists (for local development)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from .handler import PRAgentHandler


def lambda_handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: The Lambda event containing SQS message
        _: Lambda context (unused)

    Returns:
        Dict containing the processing results
    """
    try:
        # Extract message from SQS event
        if "Records" not in event:
            raise ValueError("No Records found in event")

        record = event["Records"][0]
        if "body" not in record:
            raise ValueError("No body found in record")

        # Parse message body
        try:
            message_body = json.loads(record["body"])
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in message body: {str(e)}") from e

        # Extract PR URL and command
        pr_url = message_body.get("pr_url")
        if not pr_url:
            raise ValueError("No pr_url found in message")

        # Get command, default to review if none provided
        command = message_body.get("command", "/review")

        # Process command using PR agent handler
        handler = PRAgentHandler()
        result = handler.run_command(pr_url, command)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "PR command processed successfully",
                    "pr_url": pr_url,
                    "result": result,
                }
            ),
        }

    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid request", "error": str(e)}),
        }
    except (KeyError, IndexError) as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid event structure", "error": str(e)}),
        }
    except RuntimeError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Runtime error", "error": str(e)}),
        }
