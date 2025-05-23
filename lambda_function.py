import json
import logging
from typing import Dict, Any
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize logger
logger = Logger()

@logger.inject_lambda_context
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    AWS Lambda handler function that processes SQS events.
    
    Args:
        event: The Lambda event containing SQS messages
        context: Lambda context object
    
    Returns:
        Dict containing status code and message
    """
    try:
        # Process each record from the SQS event
        for record in event.get('Records', []):
            # Extract message body
            message_body = json.loads(record['body'])
            logger.info(f"Processing message: {message_body}")
            
            # TODO: Add your message processing logic here
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed SQS messages'
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