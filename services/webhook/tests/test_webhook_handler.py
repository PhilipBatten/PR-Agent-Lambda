"""Unit tests for the webhook handler."""

import json
import os
import hmac
import hashlib
from unittest.mock import patch, MagicMock

import pytest
from webhook_lambda.handler import handler, verify_signature, process_pr_event


class MockLambdaContext:
    """Mock Lambda context for testing."""
    def __init__(self):
        self.function_name = "test-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-2:123456789012:function:test-function"
        self.aws_request_id = "test-request-id"


@pytest.fixture
def mock_env_vars():
    """Fixture for environment variables."""
    with patch.dict(os.environ, {
        'GITHUB_WEBHOOK_SECRET': 'test-secret',
        'SNS_TOPIC_ARN': 'arn:aws:sns:region:account:topic'
    }):
        yield


@pytest.fixture
def mock_sns():
    """Fixture for mocked SNS client."""
    with patch('webhook_lambda.handler.sns') as mock:
        yield mock


@pytest.fixture
def lambda_context():
    """Fixture for Lambda context."""
    return MockLambdaContext()


def test_verify_signature():
    """Test signature verification."""
    payload = b'test-payload'
    secret = 'test-secret'
    
    # Generate a valid signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Test valid signature
    assert verify_signature(payload, f"sha256={signature}", secret)
    
    # Test invalid signature
    assert not verify_signature(payload, "invalid", secret)
    assert not verify_signature(payload, f"sha256={signature}", "wrong-secret")


def test_process_pr_event():
    """Test PR event processing."""
    # Test opened PR
    event = {
        'action': 'opened',
        'pull_request': {
            'html_url': 'https://github.com/owner/repo/pull/1'
        }
    }
    result = process_pr_event(event)
    assert result == {
        'pr_url': 'https://github.com/owner/repo/pull/1',
        'commands': ['/review']
    }
    
    # Test synchronized PR
    event['action'] = 'synchronize'
    result = process_pr_event(event)
    assert result == {
        'pr_url': 'https://github.com/owner/repo/pull/1',
        'commands': ['/review']
    }
    
    # Test ignored action
    event['action'] = 'closed'
    assert process_pr_event(event) is None
    
    # Test missing PR
    event = {'action': 'opened'}
    assert process_pr_event(event) is None


def test_handler_missing_signature(mock_env_vars, lambda_context):
    """Test handler with missing signature."""
    event = {
        'headers': {},
        'body': '{}'
    }
    
    response = handler(event, lambda_context)
    assert response['statusCode'] == 401
    assert 'Missing signature' in response['body']


def test_handler_invalid_signature(mock_env_vars, lambda_context):
    """Test handler with invalid signature."""
    event = {
        'headers': {
            'X-Hub-Signature-256': 'invalid'
        },
        'body': '{}'
    }
    
    response = handler(event, lambda_context)
    assert response['statusCode'] == 401
    assert 'Invalid signature' in response['body']


def test_handler_missing_event_type(mock_env_vars, lambda_context):
    """Test handler with missing event type."""
    # Generate valid signature
    payload = b'{}'
    signature = hmac.new(
        'test-secret'.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    event = {
        'headers': {
            'X-Hub-Signature-256': f"sha256={signature}"
        },
        'body': '{}'
    }
    
    response = handler(event, lambda_context)
    assert response['statusCode'] == 400
    assert 'Missing event type' in response['body']


def test_handler_pr_event(mock_env_vars, mock_sns, lambda_context):
    """Test handler with PR event."""
    # Generate valid signature
    payload = json.dumps({
        'action': 'opened',
        'pull_request': {
            'html_url': 'https://github.com/owner/repo/pull/1'
        }
    }).encode('utf-8')
    
    signature = hmac.new(
        'test-secret'.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    event = {
        'headers': {
            'X-Hub-Signature-256': f"sha256={signature}",
            'X-GitHub-Event': 'pull_request'
        },
        'body': payload.decode('utf-8')
    }
    
    response = handler(event, lambda_context)
    assert response['statusCode'] == 200
    assert 'Event processed successfully' in response['body']
    
    # Verify SNS message
    mock_sns.publish.assert_called_once()
    call_args = mock_sns.publish.call_args[1]
    assert call_args['TopicArn'] == 'arn:aws:sns:region:account:topic'
    message = json.loads(call_args['Message'])
    assert message['pr_url'] == 'https://github.com/owner/repo/pull/1'
    assert message['commands'] == ['/review']


def test_handler_ignored_event(mock_env_vars, mock_sns, lambda_context):
    """Test handler with ignored event."""
    # Generate valid signature
    payload = json.dumps({
        'action': 'closed',
        'pull_request': {
            'html_url': 'https://github.com/owner/repo/pull/1'
        }
    }).encode('utf-8')
    
    signature = hmac.new(
        'test-secret'.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    event = {
        'headers': {
            'X-Hub-Signature-256': f"sha256={signature}",
            'X-GitHub-Event': 'pull_request'
        },
        'body': payload.decode('utf-8')
    }
    
    response = handler(event, lambda_context)
    assert response['statusCode'] == 200
    assert 'Event ignored' in response['body']
    mock_sns.publish.assert_not_called() 