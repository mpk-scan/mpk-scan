import os
import boto3
from botocore.exceptions import NoCredentialsError

class S3Manager:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        self.bucket_name = 'cs5934-g8-s3-bucket'
        self.region_name = 'us-east-1'
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=self.region_name
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

    def list_files(self):
        paginator = self.s3_client.get_paginator('list_objects_v2')
        file_list = []
        for page in paginator.paginate(Bucket=self.bucket_name):
            for obj in page.get('Contents', []):
                file_list.append(obj['Key'])
        return file_list

if __name__ == "__main__":
    s3_manager = S3Manager()
    
    # test for uploading a flat file
    s3_manager.upload_file('testing.txt', 'testing')