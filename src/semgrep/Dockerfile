FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Install Semgrep version 1.108.0
RUN pip install semgrep==1.108.0

COPY . .

