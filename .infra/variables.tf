variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "pr_agent_user_token" {
  description = "GitHub user token for PR agent"
  type        = string
  sensitive   = true
}

variable "pr_agent_openai_key" {
  description = "OpenAI API key for PR agent"
  type        = string
  sensitive   = true
} 