# AWS Lambda SQS Processor

This project contains a Python-based AWS Lambda function that processes messages from an Amazon SQS queue and runs PR agent analysis on pull requests.

## Prerequisites

Before you begin, ensure you have the following installed:

1. Docker
2. Python 3.12 or later
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
sudo apt-get install python3.12 python3.12-venv

# macOS
brew install python@3.12
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

- `lambda_function.py`: Main Lambda handler code that processes SQS events and runs PR agent
- `requirements.txt`: Python dependencies including pr-agent
- `Dockerfile`: Container definition for the Lambda function
- `test_locally.py`: Script for local testing
- `test_events/`: Directory containing test event payloads
- `Makefile`: Commands for managing the local environment
- `.infra/`: Terraform infrastructure code
  - `main.tf`: Main infrastructure configuration
  - `variables.tf`: Variable definitions
  - `outputs.tf`: Output values

## Message Format

The Lambda function expects SQS messages in the following format:

```json
{
    "pr_number": 123,
    "repository": "owner/repo",
    "action": "opened",
    "title": "Add new feature",
    "body": "This PR adds a new feature",
    "user": "username"
}
```

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

1. Send a test PR message to the SNS topic:
```bash
aws sns publish \
  --topic-arn $(terraform output -raw sns_topic_arn) \
  --message '{"pr_number": 123, "repository": "owner/repo", "action": "opened", "title": "Add new feature", "body": "This PR adds a new feature", "user": "username"}'
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