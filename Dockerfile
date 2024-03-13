FROM python:3.12.1

# First stage: Copy and extract binary file from GCS
FROM google/cloud-sdk:latest

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/cputil

RUN pwd

# Copy the CPUtil tar.gz file from GCS
RUN gsutil cp gs://cloudservice-bucket/cputil-linux-x64_v112.tar.gz cputil-linux-x64_v112.tar.gz

# Extract the tar.gz file
RUN tar -xzf cputil-linux-x64_v112.tar.gz && \
    rm cputil-linux-x64_v112.tar.gz

RUN pwd

# Next Stage

ENV PYTHONUNBUFFERED True

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r  requirements.txt

RUN ls --recursive /app/cputil/cputil-linux-x64/

ENV CLOUD_PRINTER_ENV=int

RUN pwd

RUN ls

EXPOSE 8000
CMD ["uvicorn", "print:app", "--host", "0.0.0.0", "--port", "8000"]
