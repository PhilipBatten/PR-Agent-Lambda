#!/usr/bin/env python3
"""Script to generate a valid GitHub webhook signature for testing."""

import hmac
import hashlib
import json

def generate_signature(payload: str, secret: str) -> str:
    """Generate a GitHub webhook signature."""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

if __name__ == "__main__":
    # Test secret from .env
    secret = "test-secret"
    
    # Test payload
    payload = {
        "action": "opened",
        "pull_request": {
            "html_url": "https://github.com/owner/repo/pull/1",
            "number": 1,
            "title": "Test PR",
            "body": "This is a test PR",
            "user": {
                "login": "testuser"
            },
            "head": {
                "ref": "feature/test",
                "sha": "abc123"
            },
            "base": {
                "ref": "main",
                "sha": "def456"
            }
        },
        "repository": {
            "full_name": "owner/repo",
            "name": "repo",
            "owner": {
                "login": "owner"
            }
        }
    }
    
    # Convert payload to JSON string
    payload_str = json.dumps(payload)
    
    # Generate signature
    signature = generate_signature(payload_str, secret)
    
    print(f"Payload: {payload_str}")
    print(f"Signature: {signature}")
    
    # Print the complete event for the test file
    event = {
        "headers": {
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json"
        },
        "body": payload
    }
    print("\nComplete event for test file:")
    print(json.dumps(event, indent=4)) 