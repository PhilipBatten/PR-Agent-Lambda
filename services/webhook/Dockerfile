FROM public.ecr.aws/lambda/python:3.12

# Copy requirements file
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt

# Copy function code
COPY src/webhook_lambda ${LAMBDA_TASK_ROOT}/webhook_lambda
COPY .pylintrc ${LAMBDA_TASK_ROOT}

# Set the handler
CMD [ "webhook_lambda.handler.handler" ] 