FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# disable cache dir
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
