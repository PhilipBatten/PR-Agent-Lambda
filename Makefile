.PHONY: build run stop send-event clean lint format docker-lint docker-format test-review test-describe test-ask test-test docker-test

# Variables
CONTAINER_NAME = sqs-lambda-processor
LAMBDA_PORT = 9000
PYTHON_FILES = src/pr_agent_lambda/*.py
TEST_FILES = tests/*.py

# Build the Docker image
build:
	docker build -t $(CONTAINER_NAME) .

# Run the Lambda container in detached mode with .env file if it exists
run:
	@echo "Starting Lambda container..."
	@if [ -f .env ]; then \
		echo "Found .env file, injecting environment variables..."; \
		docker run -d --name $(CONTAINER_NAME) \
			--env-file .env \
			-p $(LAMBDA_PORT):8080 $(CONTAINER_NAME) || true; \
	else \
		echo "No .env file found, running without environment variables..."; \
		docker run -d --name $(CONTAINER_NAME) \
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
		-d @test_events/review_event.json \
		-H "Content-Type: application/json" | jq .

test-describe:
	@echo "Sending describe command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @test_events/describe_event.json \
		-H "Content-Type: application/json" | jq .

test-ask:
	@echo "Sending ask command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @test_events/ask_event.json \
		-H "Content-Type: application/json" | jq .

test-test:
	@echo "Sending test command..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @test_events/test_event.json \
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
		-e PYTHONPATH=/var/task/src \
		$(CONTAINER_NAME) \
		-m pytest $(TEST_FILES) -v

# Help command
help:
	@echo "Available commands:"
	@echo "  make build       - Build the Docker image"
	@echo "  make run         - Start the Lambda container"
	@echo "  make stop        - Stop and remove the container"
	@echo "  make test-review - Send a review command test event"
	@echo "  make test-describe - Send a describe command test event"
	@echo "  make test-ask    - Send an ask command test event"
	@echo "  make test-test   - Send a test command test event"
	@echo "  make clean       - Remove the container and image"
	@echo "  make lint        - Run pylint on Python files"
	@echo "  make format      - Run black formatter on Python files"
	@echo "  make docker-lint - Run pylint in Docker"
	@echo "  make docker-format - Run black formatter in Docker"
	@echo "  make docker-test - Run tests in Docker"
	@echo "  make help        - Show this help message"

lint:
	@echo "Running pylint..."
	@pylint $(PYTHON_FILES)

format:
	@echo "Running black formatter..."
	@black $(PYTHON_FILES)

docker-lint:
	@docker run --rm --entrypoint pylint -v $(PWD):/var/task -w /var/task $(CONTAINER_NAME) $(PYTHON_FILES)

docker-format:
	@docker run --rm --entrypoint black -v $(PWD):/var/task -w /var/task $(CONTAINER_NAME) $(PYTHON_FILES) 