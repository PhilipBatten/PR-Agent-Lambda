FROM public.ecr.aws/lambda/python:3.12

# Install git
RUN dnf update -y && \
    dnf install -y git && \
    dnf clean all

# Set git environment variables
ENV GIT_PYTHON_REFRESH=quiet

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code and linter config
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY .pylintrc ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ] 