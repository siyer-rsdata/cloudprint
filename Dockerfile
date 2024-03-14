FROM python:3.12.1

# First stage: Copy and extract binary file from GCS
FROM google/cloud-sdk:latest

ENV CLOUD_PRINTER_ENV=int

COPY / /app/

WORKDIR /app/conf

RUN gsutil cp gs://cloudservice-bucket/.env_constants.int .env_constants.int

RUN cat .env_constants.int

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/cputil

# Copy the CPUtil tar.gz file from GCS
RUN gsutil cp gs://cloudservice-bucket/cputil-linux-x64_v112.tar.gz cputil-linux-x64_v112.tar.gz

# Extract the tar.gz file
RUN tar -xzf cputil-linux-x64_v112.tar.gz && \
    rm cputil-linux-x64_v112.tar.gz

# Next Stage

ENV PYTHONUNBUFFERED True

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r  requirements.txt

WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "print:app", "--host", "0.0.0.0", "--port", "8000"]
