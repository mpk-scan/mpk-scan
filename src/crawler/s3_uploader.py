import boto3
import os

# def upload_to_s3(filename, content, bucket_name="your-s3-bucket"):
#     s3 = boto3.client("s3")
    
#     # Save content to a temp file
#     temp_filepath = f"/tmp/{filename}"
#     with open(temp_filepath, "w") as file:
#         file.write(content)
    
#     # Upload to S3
#     s3.upload_file(temp_filepath, bucket_name, filename)
#     print(f"Uploaded {filename} to {bucket_name}")
    
#     # Remove temp file
#     os.remove(temp_filepath)
