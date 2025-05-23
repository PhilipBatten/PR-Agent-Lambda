import json
import os
import subprocess
from typing import Dict, List, Any, Optional

def configure_pr_agent() -> None:
    """Configure PR agent environment variables."""
    os.environ["PR_AGENT_PROVIDER"] = "github"
    os.environ["PR_AGENT_USER_TOKEN"] = os.environ.get("PR_AGENT_USER_TOKEN", "")
    os.environ["PR_AGENT_OPENAI_KEY"] = os.environ.get("PR_AGENT_OPENAI_KEY", "")

def run_pr_agent_command(pr_url: str, command: str) -> Dict[str, Any]:
    """
    Run a PR agent command and return the result.
    
    Args:
        pr_url: The URL of the pull request
        command: The PR agent command to run
        
    Returns:
        Dict containing the command result and status
    """
    try:
        # Run the PR agent command
        result = subprocess.run(
            ["pr-agent", command, pr_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success",
            "command": command,
            "output": result.stdout,
            "error": None
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "command": command,
            "output": None,
            "error": f"Command failed: {e.stderr}"
        }
    except (subprocess.SubprocessError, OSError) as e:
        return {
            "status": "error",
            "command": command,
            "output": None,
            "error": f"Process error: {str(e)}"
        }

def process_pr_commands(pr_url: str, commands: List[str]) -> List[Dict[str, Any]]:
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
        result = run_pr_agent_command(pr_url, command)
        results.append(result)
    return results

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
        # Configure PR agent
        configure_pr_agent()
        
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
        
        # Extract PR URL and commands
        pr_url = message_body.get("pr_url")
        if not pr_url:
            raise ValueError("No pr_url found in message")
            
        # Get commands, default to review if none provided
        commands = message_body.get("commands", ["/review"])
        
        # Process commands
        results = process_pr_commands(pr_url, commands)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "PR commands processed successfully",
                "pr_url": pr_url,
                "results": results
            })
        }
        
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid request",
                "error": str(e)
            })
        }
    except (OSError, subprocess.SubprocessError) as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "System error",
                "error": str(e)
            })
        } 
