.PHONY: build run stop send-event clean lint format docker-lint docker-format test-review test-describe test-ask test-test docker-test build-webhook run-webhook stop-webhook test-webhook test-webhook-local

# Variables
CONTAINER_NAME = sqs-lambda-processor
WEBHOOK_CONTAINER_NAME = webhook-lambda
LAMBDA_PORT = 9000
WEBHOOK_PORT = 9001
PYTHON_FILES = services/agent/src/pr_agent_lambda/*.py
TEST_FILES = services/agent/tests/*.py
WEBHOOK_PYTHON_FILES = services/webhook/src/webhook_lambda/*.py
WEBHOOK_TEST_FILES = services/webhook/tests/*.py
AWS_REGION = eu-west-2

# Build the Docker image
build:
	docker build -t $(CONTAINER_NAME) services/agent

# Run the Lambda container in detached mode with .env file if it exists
run:
	@echo "Starting Lambda container..."
	@if [ -f .env ]; then \
		echo "Found .env file, injecting environment variables..."; \
		docker run -d --name $(CONTAINER_NAME) \
			--env-file .env \
			-e AWS_DEFAULT_REGION=$(AWS_REGION) \
			-p $(LAMBDA_PORT):8080 $(CONTAINER_NAME) || true; \
	else \
		echo "No .env file found, running without environment variables..."; \
		docker run -d --name $(CONTAINER_NAME) \
			-e AWS_DEFAULT_REGION=$(AWS_REGION) \
			-p $(LAMBDA_PORT):8080 $(CONTAINER_NAME) || true; \
	fi
	@echo "Container started. Waiting for it to be ready..."
	@sleep 5
	@echo "Container is ready!"

# Stop and remove the container
stop:
	@echo "Stopping Lambda container..."
	@docker stop $(CONTAINER_NAME) || true
	@docker rm $(CONTAINER_NAME) || true
	@echo "Container stopped and removed."

# Send test events
test-review:
	@echo "Sending review command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @services/agent/test_events/review_event.json \
		-H "Content-Type: application/json" | jq .

test-describe:
	@echo "Sending describe command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @services/agent/test_events/describe_event.json \
		-H "Content-Type: application/json" | jq .

test-ask:
	@echo "Sending ask command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @services/agent/test_events/ask_event.json \
		-H "Content-Type: application/json" | jq .

test-test:
	@echo "Sending test command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @services/agent/test_events/test_event.json \
		-H "Content-Type: application/json" | jq .

# Clean up Docker resources
clean: stop
	@echo "Cleaning up Docker resources..."
	@docker rmi $(CONTAINER_NAME) || true
	@echo "Cleanup complete."

docker-test:
	@echo "Running tests in Docker..."
	@docker run --rm \
		--entrypoint python \
		-v $(PWD):/var/task \
		-w /var/task \
		-e PYTHONPATH=/var/task/services/agent/src \
		$(CONTAINER_NAME) \
		-m pytest $(TEST_FILES) -v

# Webhook service commands
build-webhook:
	docker build -t $(WEBHOOK_CONTAINER_NAME) services/webhook

run-webhook:
	@echo "Starting Webhook Lambda container..."
	@if [ -f .env ]; then \
		echo "Found .env file, injecting environment variables..."; \
		docker run -d --name $(WEBHOOK_CONTAINER_NAME) \
			--env-file .env \
			-e AWS_SAM_LOCAL=true \
			-e AWS_DEFAULT_REGION=$(AWS_REGION) \
			-p $(WEBHOOK_PORT):8080 $(WEBHOOK_CONTAINER_NAME) || true; \
	else \
		echo "No .env file found, running without environment variables..."; \
		docker run -d --name $(WEBHOOK_CONTAINER_NAME) \
			-e AWS_SAM_LOCAL=true \
			-e AWS_DEFAULT_REGION=$(AWS_REGION) \
			-p $(WEBHOOK_PORT):8080 $(WEBHOOK_CONTAINER_NAME) || true; \
	fi
	@echo "Container started. Waiting for it to be ready..."
	@sleep 5
	@echo "Container is ready!"

stop-webhook:
	@echo "Stopping Webhook Lambda container..."
	@docker stop $(WEBHOOK_CONTAINER_NAME) || true
	@docker rm $(WEBHOOK_CONTAINER_NAME) || true
	@echo "Container stopped and removed."

test-webhook:
	@echo "Running webhook tests in Docker..."
	@docker run --rm \
		--entrypoint python \
		-v $(PWD):/var/task \
		-w /var/task \
		-e PYTHONPATH=/var/task/services/webhook/src \
		-e AWS_DEFAULT_REGION=$(AWS_REGION) \
		$(WEBHOOK_CONTAINER_NAME) \
		-m pytest $(WEBHOOK_TEST_FILES) -v

docker-lint-webhook:
	@docker run --rm --entrypoint pylint \
		-v $(PWD):/var/task \
		-w /var/task \
		-e AWS_DEFAULT_REGION=$(AWS_REGION) \
		$(WEBHOOK_CONTAINER_NAME) $(WEBHOOK_PYTHON_FILES)

docker-format-webhook:
	@docker run --rm --entrypoint black \
		-v $(PWD):/var/task \
		-w /var/task \
		-e AWS_DEFAULT_REGION=$(AWS_REGION) \
		$(WEBHOOK_CONTAINER_NAME) $(WEBHOOK_PYTHON_FILES)

# Test webhook locally
test-webhook-local:
	@echo "Sending test PR event to webhook..."
	@curl -XPOST "http://localhost:$(WEBHOOK_PORT)/2015-03-31/functions/function/invocations" \
		-d @services/webhook/test_events/pr_event.json \
		-H "Content-Type: application/json" | jq .

# Help command
help:
	@echo "Available commands:"
	@echo "  make build       - Build the agent Docker image"
	@echo "  make run         - Start the agent Lambda container"
	@echo "  make stop        - Stop and remove the agent container"
	@echo "  make test-review - Send a review command test event"
	@echo "  make test-describe - Send a describe command test event"
	@echo "  make test-ask    - Send an ask command test event"
	@echo "  make test-test   - Send a test command test event"
	@echo "  make clean       - Remove the container and image"
	@echo "  make lint        - Run pylint on agent Python files"
	@echo "  make format      - Run black formatter on agent Python files"
	@echo "  make docker-lint - Run pylint in Docker for agent"
	@echo "  make docker-format - Run black formatter in Docker for agent"
	@echo "  make docker-test - Run tests in Docker for agent"
	@echo "  make build-webhook - Build the webhook Docker image"
	@echo "  make run-webhook - Start the webhook Lambda container"
	@echo "  make stop-webhook - Stop and remove the webhook container"
	@echo "  make test-webhook - Run tests in Docker for webhook"
	@echo "  make test-webhook-local - Send test PR event to webhook"
	@echo "  make docker-lint-webhook - Run pylint in Docker for webhook"
	@echo "  make docker-format-webhook - Run black formatter in Docker for webhook"
	@echo "  make help        - Show this help message"

lint:
	@echo "Running pylint..."
	@pylint $(PYTHON_FILES)

format:
	@echo "Running black formatter..."
	@black $(PYTHON_FILES)

docker-lint:
	@docker run --rm --entrypoint pylint \
		-v $(PWD):/var/task \
		-w /var/task \
		$(CONTAINER_NAME) $(PYTHON_FILES)

docker-format:
	@docker run --rm --entrypoint black \
		-v $(PWD):/var/task \
		-w /var/task \
		$(CONTAINER_NAME) $(PYTHON_FILES) 