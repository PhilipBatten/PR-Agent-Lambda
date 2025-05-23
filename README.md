# AWS Lambda SQS Processor

This project contains a Python-based AWS Lambda function that processes messages from an Amazon SQS queue.

## Prerequisites

Before you begin, ensure you have the following installed:

1. Docker
2. Python 3.11 or later
3. Make
4. jq (for JSON formatting in test output)
5. Terraform (for AWS deployment)
6. AWS CLI configured with appropriate credentials

### Installing Prerequisites

#### Docker
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io

# macOS
brew install docker
```

#### Python
```bash
# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# macOS
brew install python@3.11
```

#### Make
```bash
# Ubuntu/Debian
sudo apt-get install make

# macOS
brew install make
```

#### jq
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

#### Terraform
```bash
# Ubuntu/Debian
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# macOS
brew install terraform
```

#### AWS CLI
```bash
# Ubuntu/Debian
sudo apt-get install awscli

# macOS
brew install awscli
```

## Project Structure

- `lambda_function.py`: Main Lambda handler code
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container definition for the Lambda function
- `test_locally.py`: Script for local testing
- `test_events/`: Directory containing test event payloads
- `Makefile`: Commands for managing the local environment
- `.infra/`: Terraform infrastructure code
  - `main.tf`: Main infrastructure configuration
  - `variables.tf`: Variable definitions
  - `outputs.tf`: Output values

## Deployment

### AWS Infrastructure Setup

1. Initialize Terraform:
```bash
cd .infra
terraform init
```

2. Review the planned changes:
```bash
terraform plan
```

3. Apply the infrastructure:
```bash
terraform apply
```

4. After successful deployment, you'll see outputs including:
   - Lambda function name
   - SNS topic ARN
   - SQS queue URL
   - ECR repository URL

### Deploying the Lambda Function

1. Build and tag the Docker image:
```bash
make build
docker tag sqs-lambda-processor:latest $(terraform output -raw ecr_repository_url):latest
```

2. Push to ECR:
```bash
aws ecr get-login-password --region $(terraform output -raw aws_region) | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url)
docker push $(terraform output -raw ecr_repository_url):latest
```

### Testing the Deployment

1. Send a test message to the SNS topic:
```bash
aws sns publish \
  --topic-arn $(terraform output -raw sns_topic_arn) \
  --message '{"message": "Hello from SNS!"}'
```

2. Check CloudWatch Logs for the Lambda function execution:
```bash
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name)
```

## Local Testing

### Using Makefile (Recommended)

The Makefile provides convenient commands for managing the local Lambda environment:

1. Build the Docker image:
```bash
make build
```

2. Start the Lambda container:
```bash
make run
```

3. Send a test event:
```bash
make send-event
```

4. Stop the container:
```bash
make stop
```

5. Clean up all resources:
```bash
make clean
```

6. Show available commands:
```bash
make help
```

### Using Python Script

Alternatively, you can use the Python script for testing:

1. Build the Docker image:
```bash
docker build -t sqs-lambda-processor .
```

2. Install local testing dependencies:
```bash
pip install -r requirements.txt
```

3. Run the test script:
```bash
python test_locally.py
```

The test script will:
- Start the Lambda container locally
- Send a test SQS event to the function
- Display the function's response
- Clean up by stopping the container

You can modify the test event in `test_events/sqs_event.json` to test different scenarios.

## Setup and Deployment

1. Build the Docker image:
```bash
docker build -t sqs-lambda-processor .
```

2. Test locally (optional):
```bash
docker run -p 9000:8080 sqs-lambda-processor
```

3. Push to Amazon ECR:
```bash
# Create ECR repository (if not exists)
aws ecr create-repository --repository-name sqs-lambda-processor

# Login to ECR
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com

# Tag and push the image
docker tag sqs-lambda-processor:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/sqs-lambda-processor:latest
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/sqs-lambda-processor:latest
```

4. Create Lambda Function:
   - Create a new Lambda function using the container image
   - Configure the SQS trigger in the Lambda function settings
   - Set appropriate IAM roles and permissions

## Required IAM Permissions

The Lambda function requires the following permissions:
- `sqs:ReceiveMessage`
- `sqs:DeleteMessage`
- `sqs:GetQueueAttributes`
- `sqs:ChangeMessageVisibility`

## Environment Variables

No environment variables are required by default, but you can add them as needed for your specific use case.
