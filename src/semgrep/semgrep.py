import sys
import os
import time
import subprocess
from datetime import datetime
import boto3
from S3Manager import S3Manager  # Assuming S3Manager is in a separate file

# ------------------------------------------------------------------------------------------

# Constants

OUTPUT_DIR = 'output'

current_time = datetime.now().strftime("%Y%m%d-%H%M%S")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, current_time)
os.makedirs(OUTPUT_PATH, exist_ok=True)

LOG_FILE = os.path.join(OUTPUT_PATH, 'log.txt')

RULES_DIRECTORY = 'production_rules'

# ------------------------------------------------------------------------------------------

def log_print(message):
    """Append a log message to the log file in the timestamped directory."""
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def run_semgrep_on_file(file_path, output_path):
    """Run Semgrep on the file and save the output to a specified path."""
    try:
        # Run the Semgrep command and capture the output and errors
        result = subprocess.run(
            ['semgrep', file_path, '--config', RULES_DIRECTORY],
            text=True,  # Handle inputs and outputs as text (strings)
            capture_output=True  # Capture stdout and stderr
        )
        
        # Check if there were any errors
        if result.stderr:
            log_print("ERROR: ", result.stderr)

        # Write the output to the file
        with open(output_path, 'w') as output_file:
            output_file.write(result.stdout)

    except Exception as e:
        # Log any exceptions that might occur during the subprocess execution
        log_print("An exception occurred: ", str(e))

def run_all():
    """Run Semgrep on all the files"""
    s3_manager = S3Manager()

    file_list = s3_manager.list_files()

    log_print("Fetched all filenames from the S3 bucket.")

    for file_key in file_list:
        # Sanitize the file name to avoid issues with reserved characters
        safe_file_key = sanitize_filename(file_key)
        # Temporary file path
        temp_file_path = os.path.join('/tmp', safe_file_key.replace('/', '_'))
        
        # Download the file
        s3_manager.download_file(file_key, temp_file_path)
        
        # Run Semgrep and output the results to the specified output directory
        output_file_path = os.path.join(OUTPUT_PATH, f"{os.path.basename(safe_file_key)}_result.txt")
        run_semgrep_on_file(temp_file_path, output_file_path)
        
        # Delete the temporary file
        os.remove(temp_file_path)

        log_print(f"Semgrep complete for file: {file_key}")

def sanitize_filename(filename):
    """Sanitize the filename by replacing unsafe characters."""
    return filename.replace('|', '_')

# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------

def main():
    run_all()

if __name__ == "__main__":
    main()
