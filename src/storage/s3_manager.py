
import os
import boto3
from botocore.exceptions import NoCredentialsError

class S3Manager:
    def __init__(self, bucket_name, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=region_name
        )

    def upload_file(self, file_name, object_name=None):
        if object_name is None:
            object_name = file_name
        try:
            self.s3_client.upload_file(file_name, self.bucket_name, object_name)
            print(f"File {file_name} uploaded to {self.bucket_name}/{object_name}")
        except NoCredentialsError:
            print("Credentials not available")

    def download_file(self, object_name, file_name=None):
        if file_name is None:
            file_name = object_name
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_name)
            print(f"File {object_name} downloaded from {self.bucket_name} to {file_name}")
        except NoCredentialsError:
            print("Credentials not available")

if __name__ == "__main__":
    bucket_name = 'cs5934-g8-s3-bucket'
    region_name = 'us-east-1'

    s3_manager = S3Manager(bucket_name, region_name=region_name)
    
    # test for uploading a flat file
    s3_manager.upload_file('testing.txt', 'testing')