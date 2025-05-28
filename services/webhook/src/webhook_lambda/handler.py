"""GitHub webhook handler for processing repository events."""

import json
import hmac
import hashlib
import os
from typing import Dict, Any, Optional

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize logger
logger = Logger()

class WebhookError(Exception):
    """Base exception for webhook errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class ValidationError(WebhookError):
    """Exception for validation errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class AuthenticationError(WebhookError):
    """Exception for authentication errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

class ConfigurationError(WebhookError):
    """Exception for configuration errors."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)

# Initialize SNS client
if os.getenv("AWS_SAM_LOCAL") or os.getenv("LOCALSTACK_HOSTNAME"):
    # Use a mock SNS client for local testing
    class MockSNS:
        """Mock SNS client for local testing."""
        def __init__(self):
            """Initialize the mock SNS client."""
            self.published_messages = []

        def publish(self, **kwargs) -> Dict[str, str]:
            """Mock the publish method to log the message and return a mock ID."""
            logger.info("Mock SNS publish", extra=kwargs)
            self.published_messages.append(kwargs)
            return {"MessageId": "mock-message-id"}

        def get_published_messages(self) -> list:
            """Get all published messages for testing."""
            return self.published_messages

        def clear_messages(self) -> None:
            """Clear all published messages."""
            self.published_messages = []

    sns = MockSNS()
else:
    # Use real SNS client in AWS
    sns = boto3.client("sns")

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify the GitHub webhook signature.

    Args:
        payload: The raw request payload
        signature: The signature from the X-Hub-Signature-256 header
        secret: The webhook secret

    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature or not secret:
        logger.warning("Missing signature or secret")
        return False

    expected_signature = hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()

    actual_signature = signature.replace("sha256=", "")
    expected_signature = expected_signature.replace("sha256=", "")

    logger.debug(
        "Signature verification",
        extra={"expected": expected_signature, "actual": actual_signature},
    )

    return hmac.compare_digest(f"sha256={expected_signature}", signature)

def process_pr_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a pull request event and create an SNS message.

    Args:
        event: The GitHub webhook event

    Returns:
        Optional[Dict[str, Any]]: The SNS message if it's a PR event, None otherwise
    """
    if event.get("action") not in ["opened", "synchronize"]:
        return None

    pr = event.get("pull_request", {})
    if not pr:
        return None

    return {
        "pr_url": pr.get("html_url"),
        "commands": ["/review"],  # Default command for new PRs
    }

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        message: Error message

    Returns:
        Dict[str, Any]: The error response
    """
    return {"statusCode": status_code, "body": json.dumps({"error": message})}

def create_success_response(message: str) -> Dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        message: Success message

    Returns:
        Dict[str, Any]: The success response
    """
    return {"statusCode": 200, "body": json.dumps({"message": message})}

def validate_webhook_request(event: Dict[str, Any]) -> tuple[str, str, str]:
    """
    Validate the webhook request and return required components.

    Args:
        event: The Lambda event

    Returns:
        tuple[str, str, str]: The signature, webhook secret, and event type

    Raises:
        AuthenticationError: If signature is missing or invalid
        ConfigurationError: If required environment variables are missing
        ValidationError: If event type is missing
    """
    # Get the GitHub signature
    signature = event.get("headers", {}).get("X-Hub-Signature-256")
    if not signature:
        raise AuthenticationError("Missing signature")

    # Get the webhook secret
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        raise ConfigurationError("Missing GITHUB_WEBHOOK_SECRET environment variable")

    # Get the event type
    event_type = event.get("headers", {}).get("X-GitHub-Event")
    if not event_type:
        raise ValidationError("Missing event type")

    return signature, webhook_secret, event_type

@logger.inject_lambda_context
def handler(event: Dict[str, Any], _context: LambdaContext) -> Dict[str, Any]:
    """
    Handle GitHub webhook events.

    Args:
        event: The Lambda event
        _context: The Lambda context (unused)

    Returns:
        Dict[str, Any]: The response
    """
    try:
        logger.info(
            "Received webhook event",
            extra={"event_type": event.get("headers", {}).get("X-GitHub-Event")},
        )

        # Validate request and get components
        signature, webhook_secret, event_type = validate_webhook_request(event)

        # Get and process the body
        body = event.get("body", {})
        body_str = json.dumps(body) if isinstance(body, dict) else body

        # Verify the signature
        if not verify_signature(body_str.encode("utf-8"), signature, webhook_secret):
            logger.warning(
                "Invalid signature",
                extra={"signature": signature, "body_length": len(body_str)},
            )
            raise AuthenticationError("Invalid signature")

        # Process the event
        body_data = body if isinstance(body, dict) else json.loads(body_str)
        if event_type == "pull_request":
            sns_message = process_pr_event(body_data)
            if sns_message:
                # Get the SNS topic ARN
                topic_arn = os.getenv("SNS_TOPIC_ARN")
                if not topic_arn:
                    raise ConfigurationError("Missing SNS_TOPIC_ARN environment variable")

                # Publish to SNS
                logger.info(
                    "Publishing to SNS", extra={"pr_url": sns_message["pr_url"]}
                )
                sns.publish(TopicArn=topic_arn, Message=json.dumps(sns_message))
                return create_success_response("Event processed successfully")

        return create_success_response("Event ignored")

    except WebhookError as e:
        logger.warning(f"Webhook error: {str(e)}")
        return create_error_response(e.status_code, e.message)
    except json.JSONDecodeError as e:
        logger.exception("Error decoding JSON")
        return create_error_response(400, f"Invalid JSON: {str(e)}")
    except (ValueError, KeyError) as e:
        logger.exception("Error processing event data")
        return create_error_response(400, f"Invalid event data: {str(e)}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error processing webhook")
        return create_error_response(500, "Internal server error")
