import subprocess
import sys
import os
import jsbeautifier
import requests
import concurrent.futures
import threading
import hashlib
import time
from urllib.parse import urljoin, urlparse
from .html_parser import extract_javascript
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

# Optional research headers, set via env so no identity is hardcoded.
# e.g. MPK_SCAN_RESEARCH_ID=your-handle MPK_SCAN_BUG_BOUNTY_PROGRAM=program-name
BB_HEADERS = {"User-Agent": "mpk-scan/1.0"}
_RESEARCH_ID = os.getenv("MPK_SCAN_RESEARCH_ID", "")
_BUG_BOUNTY_PROGRAM = os.getenv("MPK_SCAN_BUG_BOUNTY_PROGRAM", "")
if _RESEARCH_ID:
    BB_HEADERS["X-HackerOne-Research"] = _RESEARCH_ID
    BB_HEADERS["User-Agent"] = f"mpk-scan-research {_RESEARCH_ID}"
if _BUG_BOUNTY_PROGRAM:
    BB_HEADERS["X-Bug-Bounty"] = _BUG_BOUNTY_PROGRAM

session = requests.Session()
session.headers.update(BB_HEADERS)

SKIP_THIRD_PARTY = ["adobedtm.com", "trustarc.com", "hlx.page", "consent.", "googletagmanager.com", "hotjar.com", "segment.io", "intercom.io"]

# Serialize all outbound requests across worker threads. A 250 ms minimum
# start-to-start interval keeps the whole process at no more than 4 rps.
REQUEST_INTERVAL_SECONDS = float(os.getenv("MPK_SCAN_REQUEST_INTERVAL_SECONDS", "0.25"))
_REQUEST_LOCK = threading.Lock()
_LAST_REQUEST_STARTED = 0.0

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


def throttled_get(url, **kwargs):
    """Issue a GET while enforcing the process-wide request-rate ceiling."""
    global _LAST_REQUEST_STARTED
    with _REQUEST_LOCK:
        wait = REQUEST_INTERVAL_SECONDS - (time.monotonic() - _LAST_REQUEST_STARTED)
        if wait > 0:
            time.sleep(wait)
        _LAST_REQUEST_STARTED = time.monotonic()
    return requests.get(url, **kwargs)


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

    response = throttled_get(url, timeout=5, headers=BB_HEADERS)
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

                if any(skip in external_url for skip in SKIP_THIRD_PARTY):
                    log_print(f"[SKIP] 3rd-party filtered: {external_url}")
                    continue
                # Check for duplicate external
                if external_url not in external_files:
                    response = throttled_get(external_url, headers=BB_HEADERS, timeout=5)
                    if response.status_code != 200:
                        continue
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
