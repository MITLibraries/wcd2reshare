FROM public.ecr.aws/lambda/python:3.9

# Copy function code
COPY . ${LAMBDA_TASK_ROOT}/


# Default handler. See README for how to override to a different handler.
CMD [ "wcd2reshare.lambda_handler" ]