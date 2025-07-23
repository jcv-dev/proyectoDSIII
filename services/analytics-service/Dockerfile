# Base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /code

# Set Python path to include the working directory
ENV PYTHONPATH=/code

# Copy requirements and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application code
COPY ./app.py /code/app.py

# Command to run the application using uvicorn
# The port will be exposed by Kubernetes
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
