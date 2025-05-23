import json
import logging
import os
from typing import Dict, Any, List
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from pr_agent import cli
from pr_agent.config_loader import get_settings

# Initialize logger
logger = Logger()

def configure_pr_agent():
    """Configure PR Agent with environment variables"""
    settings = get_settings()
    
    # Get configuration from environment variables
    provider = os.getenv('PR_AGENT_PROVIDER', 'github')
    user_token = os.getenv('PR_AGENT_USER_TOKEN')
    openai_key = os.getenv('PR_AGENT_OPENAI_KEY')
    
    if not all([user_token, openai_key]):
        raise ValueError("Missing required environment variables: PR_AGENT_USER_TOKEN and PR_AGENT_OPENAI_KEY")
    
    # Set the configurations
    settings.set("CONFIG.git_provider", provider)
    settings.set("openai.key", openai_key)
    settings.set("github.user_token", user_token)
    
    return settings

def process_pr_commands(pr_url: str, commands: List[str]) -> Dict[str, Any]:
    """
    Process multiple PR agent commands for a given PR URL.
    
    Args:
        pr_url: The URL of the PR to process
        commands: List of commands to run (e.g., ['/review', '/describe', '/improve'])
    
    Returns:
        Dict containing results for each command
    """
    results = {}
    
    for command in commands:
        try:
            logger.info(f"Running command '{command}' on PR: {pr_url}")
            cli.run_command(pr_url, command)
            results[command] = "success"
            logger.info(f"Successfully executed command '{command}' on PR: {pr_url}")
        except Exception as e:
            error_msg = f"Error executing command '{command}': {str(e)}"
            logger.error(error_msg)
            results[command] = f"error: {str(e)}"
    
    return results

@logger.inject_lambda_context
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    AWS Lambda handler function that processes SQS events and runs PR agent commands.
    
    Args:
        event: The Lambda event containing SQS messages
        context: Lambda context object
    
    Returns:
        Dict containing status code and message
    """
    try:
        # Configure PR Agent
        configure_pr_agent()
        
        all_results = {}
        
        # Process each record from the SQS event
        for record in event.get('Records', []):
            # Extract message body
            message_body = json.loads(record['body'])
            logger.info(f"Processing message: {message_body}")
            
            # Extract PR information
            pr_url = message_body.get('pr_url')
            commands = message_body.get('commands', ['/review'])  # Default to review command
            
            if not pr_url:
                raise ValueError("Missing required field: pr_url")
            
            # Process all commands for this PR
            pr_results = process_pr_commands(pr_url, commands)
            all_results[pr_url] = pr_results
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed PR commands',
                'results': all_results
            })
        }
    
    except Exception as e:
        logger.exception("Error processing SQS messages")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error processing messages: {str(e)}'
            })
        } 