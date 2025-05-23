import json
import requests
import time
import subprocess
import os
import signal
import sys

def start_lambda_container():
    """Start the Lambda container in the background"""
    print("Starting Lambda container...")
    process = subprocess.Popen(
        ["docker", "run", "-p", "9000:8080", "sqs-lambda-processor"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def stop_lambda_container(process):
    """Stop the Lambda container"""
    print("\nStopping Lambda container...")
    process.terminate()
    process.wait()

def send_test_event():
    """Send a test event to the local Lambda function"""
    # Load the test event
    with open('test_events/sqs_event.json', 'r') as f:
        test_event = json.load(f)
    
    # Send the event to the local Lambda function
    response = requests.post(
        "http://localhost:9000/2015-03-31/functions/function/invocations",
        json=test_event
    )
    
    return response.json()

def main():
    # Start the Lambda container
    container_process = start_lambda_container()
    
    try:
        # Wait for the container to start
        print("Waiting for container to start...")
        time.sleep(5)
        
        # Send test event
        print("\nSending test event...")
        response = send_test_event()
        
        # Print the response
        print("\nLambda Response:")
        print(json.dumps(response, indent=2))
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {str(e)}")
    finally:
        # Stop the container
        stop_lambda_container(container_process)

if __name__ == "__main__":
    main() 