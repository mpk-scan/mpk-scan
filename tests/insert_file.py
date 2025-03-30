from s3_manager import S3Manager

# Create an instance of the S3 manager
s3 = S3Manager()

# File(s) to upload
files_to_insert = {
    "/home/remy1/Desktop/grad_cap/semgrep_playground/path_traversal/test_traversal.js",
    "/home/remy1/Desktop/grad_cap/semgrep_playground/jeremy/bad-origin-checks/mini-bad-origin-checks.js",
    "/home/remy1/Desktop/grad_cap/semgrep_playground/jeremy/test_production_rules/test_eval.js"
}

# Upload each file
for file in files_to_insert:
    s3.upload_file(file)
