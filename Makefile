.PHONY: build run stop send-event clean

# Variables
CONTAINER_NAME = sqs-lambda-processor
LAMBDA_PORT = 9000

# Build the Docker image
build:
	docker build -t $(CONTAINER_NAME) .

# Run the Lambda container in detached mode
run:
	@echo "Starting Lambda container..."
	@docker run -d --name $(CONTAINER_NAME) -p $(LAMBDA_PORT):8080 $(CONTAINER_NAME) || true
	@echo "Container started. Waiting for it to be ready..."
	@sleep 5
	@echo "Container is ready!"

# Stop and remove the container
stop:
	@echo "Stopping Lambda container..."
	@docker stop $(CONTAINER_NAME) || true
	@docker rm $(CONTAINER_NAME) || true
	@echo "Container stopped and removed."

# Send a test event to the running container
send-event:
	@echo "Sending test event..."
	@curl -XPOST "http://localhost:$(LAMBDA_PORT)/2015-03-31/functions/function/invocations" \
		-d @test_events/sqs_event.json \
		-H "Content-Type: application/json" | jq .

# Clean up Docker resources
clean: stop
	@echo "Cleaning up Docker resources..."
	@docker rmi $(CONTAINER_NAME) || true
	@echo "Cleanup complete."

# Help command
help:
	@echo "Available commands:"
	@echo "  make build       - Build the Docker image"
	@echo "  make run         - Start the Lambda container"
	@echo "  make stop        - Stop and remove the container"
	@echo "  make send-event  - Send a test event to the running container"
	@echo "  make clean       - Remove the container and image"
	@echo "  make help        - Show this help message" 