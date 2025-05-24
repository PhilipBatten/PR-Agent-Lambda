"""PR Agent handler for processing GitHub PRs."""

import os
from typing import Dict, List, Any, Optional

from pr_agent import cli
from pr_agent.config_loader import get_settings


class PRAgentHandler:
    """Handles PR agent operations for GitHub PRs."""

    def __init__(self):
        """Initialize the PR agent handler."""
        self._configure_environment()

    def _configure_environment(self) -> None:
        """Configure PR agent environment variables."""
        settings = get_settings()

        # Get configuration from environment variables
        provider = os.getenv("PR_AGENT_PROVIDER", "github")
        user_token = os.getenv("PR_AGENT_USER_TOKEN")
        openai_key = os.getenv("PR_AGENT_OPENAI_KEY")

        if not all([user_token, openai_key]):
            raise ValueError(
                "Missing required environment variables: PR_AGENT_USER_TOKEN and PR_AGENT_OPENAI_KEY"
            )

        # Set the configurations
        settings.set("CONFIG.git_provider", provider)
        settings.set("openai.key", openai_key)
        settings.set("github.user_token", user_token)

    def run_command(
        self, 
        pr_url: str, 
        command: str, 
        openai_key: Optional[str] = None,
        openai_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a PR agent command and return the result.

        Args:
            pr_url: The URL of the pull request
            command: The PR agent command to run
            openai_key: Optional override for OpenAI API key
            openai_model: Optional override for OpenAI model

        Returns:
            Dict containing the command result and status
        """
        try:
            # Apply any OpenAI overrides if provided
            if openai_key or openai_model:
                settings = get_settings()
                if openai_key:
                    settings.set("openai.key", openai_key)
                if openai_model:
                    settings.set("openai.model", openai_model)

            # Run the PR agent command
            cli.run_command(pr_url, command)

            return {
                "status": "success",
                "command": command,
                "output": "Command executed successfully. Check PR comments for feedback.",
                "error": None,
            }
        except ValueError as e:
            return {
                "status": "error",
                "command": command,
                "output": None,
                "error": f"Invalid input: {str(e)}",
            }
        except RuntimeError as e:
            return {
                "status": "error",
                "command": command,
                "output": None,
                "error": f"Runtime error: {str(e)}",
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            return {
                "status": "error",
                "command": command,
                "output": None,
                "error": f"Unexpected error: {str(e)}",
            }

    def process_commands(
        self, pr_url: str, commands: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple PR agent commands for a given PR URL.

        Args:
            pr_url: The URL of the pull request
            commands: List of PR agent commands to run

        Returns:
            List of results for each command
        """
        results = []
        for command in commands:
            result = self.run_command(pr_url, command)
            results.append(result)
        return results
