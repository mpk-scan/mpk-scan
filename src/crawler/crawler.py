import subprocess
import sys
import os
import jsbeautifier
import requests
import concurrent.futures
import hashlib
from urllib.parse import urljoin, urlparse
from html_parser import extract_javascript
import argparse
from datetime import datetime

# ------------------------------------------------------------------------------------------

# Output directory

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

CURRENT_TIME = datetime.now().strftime("%Y%m%d-%H%M%S")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, CURRENT_TIME)
os.makedirs(OUTPUT_PATH, exist_ok=True)

# Logging

LOG_FILE = os.path.join(OUTPUT_PATH, 'log.txt')

# Import S3 API

STORAGE_PATH = os.path.join(SCRIPT_DIR, "..", "storage")
sys.path.append(os.path.abspath(STORAGE_PATH))

from name_file import name_js, name_with_external, name_inline

from s3_manager import S3Manager

# Temp directory

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)

session = requests.Session()

# Initialize variables

files = []

external_files = []

s3 = S3Manager()

# ------------------------------------------------------------------------------------------

def log_print(message):
    """Append a log message to the log file in the timestamped directory."""
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

def run_hakrawler(domain):
    """Runs Hakrawler with subdomain exploration enabled."""
    log_print(f"Running Hakrawler on {domain}")

    # Add 'https://' if needed
    if not domain.startswith('http') and not domain.startswith('https'):
        domain = 'https://' + domain

    result = subprocess.run(
        ["hakrawler", "-subs", '-u'],
        input=domain,
        capture_output=True,
        text=True
    )

    urls = {
        line.strip().rstrip('/')
        for line in result.stdout.splitlines()
        if line.strip().startswith(("http://", "https://"))
    }

    log_print(f"Discovered {len(urls)} URLs")
    return urls

def process_url(url, no_external=False):
    '''For a given url, extract all js associated with it (inline and external)'''

    response = session.get(url, timeout=5)
    if response.status_code != 200:
        return
    content_type = response.headers.get('Content-Type', '')

    #If url is a js file
    if url.endswith('.js') or 'javascript' in content_type:
        temp_filename = hashlib.sha256(url.encode()).hexdigest()
        save_js_file(temp_filename, response.text, name_js(url))
        
    # If url is other
    elif 'text/html' in content_type:
        inline_js, external_js_links = extract_javascript(url, response.text)
        # Fetch inline JS
        if inline_js:
            temp_filename = hashlib.sha256(url.encode()).hexdigest()
            save_js_file(temp_filename, inline_js, name_inline(url))
        
        # Fetch external JS

        # if -noex or --no-external flag was present
        if no_external:
            return
        
        for js_url in external_js_links:
                external_url = urljoin(url, js_url)  # Resolve relative URLs

                # Check for duplicate external
                if external_url not in external_files:
                    response = requests.get(external_url)
                    if response.status_code != 200:
                        return  
                    content_type = response.headers.get('Content-Type', '')
                    if external_url.endswith('.js') or 'javascript' in content_type:
                        external_files.append(external_url)
                        temp_filename = hashlib.sha256((url+external_url).encode()).hexdigest()
                        save_js_file(temp_filename, response.text, name_with_external(url, external_url))


# Save temp file and upload to s3
def save_js_file(temp_name, content, filename):   
    filepath = os.path.join(TEMP_DIR, temp_name)
    beautified_code = jsbeautifier.beautify(content)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    beautified_code = "// " + timestamp + "\n\n" + beautified_code
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(beautified_code)
    s3.upload_file(filepath, filename)
    os.remove(filepath)
    log_print(f'Successfully uploaded: filepath: {filepath}, filename: {filename} to the S3 bucket')


def parse_args():
    parser = argparse.ArgumentParser(description="Run Hakrawler and extract JS files from URLs.")
    parser.add_argument(
        "-f", "--file",
        type=str,
        default="urls.txt",
        help="Path to the input file containing target domains (default: urls.txt)"
    )
    parser.add_argument(
        "--no-external", "-noex",
        action="store_true",
        help="If set, do NOT fetch or process external JavaScript files"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_file = args.file

    if not os.path.exists(input_file):
        log_print(f"File '{input_file}' not found.")
        sys.exit(1)
   
    with open(input_file, "r") as f:
        lines = f.readlines()

    target_domains = [line.strip() for line in lines]
    
    urls = [] # For printing hackrawler output, for local use
    for domain in target_domains:
        external_files = []
        urls = run_hakrawler(domain)
        # Process URLs in parallel (Change workers if needed)
        log_print("Uploading to the bucket...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(lambda u: process_url(u, args.no_external), urls)

    log_print("Complete!")



if __name__ == "__main__":
    main()
