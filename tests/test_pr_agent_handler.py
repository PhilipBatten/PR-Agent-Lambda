"""Unit tests for the PR Agent Handler."""

import os
import pytest
from unittest.mock import patch, MagicMock

from pr_agent_lambda.handler import PRAgentHandler


@pytest.fixture
def mock_settings():
    """Fixture for mocked settings."""
    with patch("pr_agent_lambda.handler.get_settings") as mock:
        settings = MagicMock()
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_cli():
    """Fixture for mocked CLI."""
    with patch("pr_agent_lambda.handler.cli") as mock:
        yield mock


@pytest.fixture
def handler(mock_settings):
    """Fixture for PRAgentHandler with mocked dependencies."""
    with patch.dict(os.environ, {
        "PR_AGENT_PROVIDER": "github",
        "PR_AGENT_USER_TOKEN": "test-token",
        "PR_AGENT_OPENAI_KEY": "test-openai-key"
    }):
        return PRAgentHandler()


def test_init_success(handler, mock_settings):
    """Test successful initialization of PRAgentHandler."""
    mock_settings.set.assert_any_call("CONFIG.git_provider", "github")
    mock_settings.set.assert_any_call("openai.key", "test-openai-key")
    mock_settings.set.assert_any_call("github.user_token", "test-token")


def test_init_missing_env_vars():
    """Test initialization fails with missing environment variables."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Missing required environment variables"):
            PRAgentHandler()


def test_run_command_success(handler, mock_cli, mock_settings):
    """Test successful command execution."""
    pr_url = "https://github.com/owner/repo/pull/1"
    command = "review"
    
    result = handler.run_command(pr_url, command)
    
    mock_cli.run_command.assert_called_once_with(pr_url, command)
    assert result["status"] == "success"
    assert result["command"] == command
    assert result["output"] == "Command executed successfully. Check PR comments for feedback."
    assert result["error"] is None


def test_run_command_with_openai_overrides(handler, mock_cli, mock_settings):
    """Test command execution with OpenAI overrides."""
    pr_url = "https://github.com/owner/repo/pull/1"
    command = "review"
    openai_key = "override-key"
    openai_model = "gpt-4"
    
    result = handler.run_command(pr_url, command, openai_key, openai_model)
    
    mock_settings.set.assert_any_call("openai.key", openai_key)
    mock_settings.set.assert_any_call("openai.model", openai_model)
    mock_cli.run_command.assert_called_once_with(pr_url, command)
    assert result["status"] == "success"


def test_run_command_value_error(handler, mock_cli):
    """Test command execution with ValueError."""
    pr_url = "https://github.com/owner/repo/pull/1"
    command = "invalid-command"
    mock_cli.run_command.side_effect = ValueError("Invalid command")
    
    result = handler.run_command(pr_url, command)
    
    assert result["status"] == "error"
    assert result["command"] == command
    assert result["output"] is None
    assert "Invalid input" in result["error"]


def test_run_command_runtime_error(handler, mock_cli):
    """Test command execution with RuntimeError."""
    pr_url = "https://github.com/owner/repo/pull/1"
    command = "review"
    mock_cli.run_command.side_effect = RuntimeError("Runtime error")
    
    result = handler.run_command(pr_url, command)
    
    assert result["status"] == "error"
    assert result["command"] == command
    assert result["output"] is None
    assert "Runtime error" in result["error"]


def test_run_command_unexpected_error(handler, mock_cli):
    """Test command execution with unexpected error."""
    pr_url = "https://github.com/owner/repo/pull/1"
    command = "review"
    mock_cli.run_command.side_effect = Exception("Unexpected error")
    
    result = handler.run_command(pr_url, command)
    
    assert result["status"] == "error"
    assert result["command"] == command
    assert result["output"] is None
    assert "Unexpected error" in result["error"]


def test_process_commands(handler, mock_cli):
    """Test processing multiple commands."""
    pr_url = "https://github.com/owner/repo/pull/1"
    commands = ["review", "describe"]
    
    results = handler.process_commands(pr_url, commands)
    
    assert len(results) == 2
    assert all(result["status"] == "success" for result in results)
    assert mock_cli.run_command.call_count == 2 