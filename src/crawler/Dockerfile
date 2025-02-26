FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# disable casche dir
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# # Set the entrypoint to run the crawler
# ENTRYPOINT ["python", "crawler.py"]