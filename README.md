# PR Agent Lambda

This AWS Lambda function processes messages from an SNS topic, triggering a review of a GitHub Merge Request (MR) using the `pr-agent` package.

## Overview

- **Purpose**: Automate the review of GitHub MRs by processing SNS messages.
- **Integration**: Receives SNS messages containing the MR URL and commands to execute.
- **Functionality**: Uses the `pr-agent` CLI to run commands like `/review`, `/describe`, and `/improve` on the specified MR.

## Prerequisites

- AWS account with Lambda and SNS access.
- GitHub token and OpenAI key for `pr-agent`.
- Docker for local testing.

## Setup

1. **Environment Variables**:
   - Set `PR_AGENT_USER_TOKEN` and `PR_AGENT_OPENAI_KEY` in AWS Secrets Manager or Parameter Store.
   - For local development, create a `.env` file with these variables.

2. **Deployment**:
   - Deploy the Lambda using Terraform:
     ```bash
     terraform apply -var="pr_agent_user_token=your_github_token" -var="pr_agent_openai_key=your_openai_key"
     ```

3. **SNS Message Format**:
   - Send a message to the SNS topic with the following JSON structure:
     ```json
     {
       "pr_url": "https://github.com/your-repo/your-pr",
       "commands": ["/review", "/describe", "/improve"]
     }
     ```

## Local Testing

- Build and run the Docker container:
  ```bash
  make build
  make run
  ```

- Send a test event:
  ```bash
  make send-event
  ```

## License

MIT