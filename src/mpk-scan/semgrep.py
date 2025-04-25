import sys
import os
import time
import subprocess
import requests
from datetime import datetime
import boto3
import argparse
import hashlib
import shutil
import jsbeautifier
from urllib.parse import urljoin, urlparse
import concurrent.futures
import tldextract

# ------------------------------------------------------------------------------------------

OUTPUT_DIR = 'output/logs'

TEMP_DIR = 'output/temp'
os.makedirs(TEMP_DIR, exist_ok=True)

CURRENT_TIME = datetime.now().strftime("%Y%m%d-%H%M%S")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, CURRENT_TIME)
os.makedirs(OUTPUT_PATH, exist_ok=True)

LOG_FILE = os.path.join(OUTPUT_PATH, 'log.txt')

DEFAULT_RULES_DIRECTORY = "production_rules"

# Import file from other directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = os.path.join(SCRIPT_DIR, "..", "storage")
CRAWLER_PATH = os.path.join(SCRIPT_DIR, '..', "crawler")
sys.path.append(os.path.abspath(STORAGE_PATH))
sys.path.append(os.path.abspath(CRAWLER_PATH))

from s3_manager import S3Manager
from name_file import name_js, name_with_external, name_inline
from unname_file import unname_js
from html_parser import extract_javascript
from crawler import run_hakrawler

# ------------------------------------------------------------------------------------------

def log_print(message):
    """Append a log message to the log file in the timestamped directory."""
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

class SemgrepAPI:

    def __init__(self, rules, search):
        # Attributes
        self.vuln_count = 0

        # For local
        self.external_files = []

        # The list of URLs/files to run semgrep on.
        # This is not "domains", because these can be prefix searches for the s3 bucket
        # ex. -s example.com/||sub/||parent-sub/files/test, which is parent-sub.sub.example.com/files/test or any subsequent paths/files
        self.search = search

        if rules == None:
            self.rules = DEFAULT_RULES_DIRECTORY
        else:
            self.rules = rules

        if self.search == None:
            log_print("No domains or prefix searches provided, searching the whole bucket.")
        else:
            log_print('Using prefix search on: ' + str(self.search))
        log_print('Running with rules: ' + str(self.rules))

    # ----------------------- HAKRAWLER -------------------------------
    def run_hakrawler_all(self):
        log_print("Running hakrawler...")
        domains = []
        for domain in self.search:
            urls = run_hakrawler(domain)
            # Process URLs in parallel (Change workers if needed)
            log_print(f"{len(urls)} URLs fetched from {domain}")
            for url in urls:
                domains.append(url)
        self.search = domains
    
    # ----------------------- LOCAL -------------------------------
    def run_all_local(self, no_external):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            log_print("Processing files in parallel...")
            futures = [executor.submit(self.process_url, url, no_external=no_external) for url in self.search]
            for future in concurrent.futures.as_completed(futures):
                future.result()

    def process_url(self,url, no_external=False):
        '''For a given url, extract all js associated with it (inline and external)'''
        log_print(f"Processing {url}...")
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return
        except requests.exceptions.RequestException as e:
            log_print(f"[ERROR] Failed to fetch {url}: {e}")
            return

        content_type = response.headers.get('Content-Type', '')

        #If url is a js file
        if url.endswith('.js') or 'javascript' in content_type:
            temp_filename = hashlib.sha256((url).encode()).hexdigest() + '.js'
            self.save_and_run_semgrep(temp_filename, response.text, url)
            
        # If url is other
        elif 'text/html' in content_type:
            inline_js, external_js_links = extract_javascript(url, response.text)
            # Fetch inline JS
            if inline_js:
                temp_filename = hashlib.sha256((url).encode()).hexdigest() + '.js'
                self.save_and_run_semgrep(temp_filename, inline_js, url)
            
            # Fetch external JS

            # if -noex or --no-external flag was present
            if no_external:
                return
            
            for js_url in external_js_links:
                    external_url = urljoin(url, js_url)  # Resolve relative URLs

                    # Check for duplicate external
                    if external_url not in self.external_files:
                        try:
                            response = requests.get(url, timeout=5)
                            if response.status_code != 200:
                                return
                        except requests.exceptions.RequestException as e:
                            log_print(f"[ERROR] Failed to fetch {url}: {e}")
                            return
                    
                        content_type = response.headers.get('Content-Type', '')
                        if external_url.endswith('.js') or 'javascript' in content_type:
                            self.external_files.append(external_url)
                            temp_filename = hashlib.sha256((url + external_url).encode()).hexdigest() + '.js'
                            self.save_and_run_semgrep(temp_filename, response.text, name_with_external(url, external_url))

    # Save temp file
    def save_and_run_semgrep(self, temp_name, content, url):   
        temp_filepath = os.path.join(TEMP_DIR, temp_name)
        beautified_code = jsbeautifier.beautify(content)
        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(beautified_code)

        clean_url = url.removeprefix("https://").removeprefix("http://")
        file_type_and_name = unname_js(clean_url)
        self.run_semgrep_on_file(temp_filepath, file_type_and_name[0], file_type_and_name[1])
        

    # ----------------------- BUCKET -------------------------------
    def run_all_from_bucket(self):
        """Run Semgrep on all the files"""
        s3_manager = S3Manager()

        if not self.search:
            file_list = s3_manager.list_files()
        else:
            self.search = remove_https(self.search)
            file_list = s3_manager.list_files_filtered(self.search)

        log_print("Processing files in parallel...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(self.process_parallel_bucket, s3_manager, file_key)
                for file_key in file_list
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()


    def process_parallel_bucket(self, s3_manager, file_key):
        hash_file_key = hashlib.sha256(file_key.encode()).hexdigest() + '.js'

        temp_file_path = os.path.join(TEMP_DIR, hash_file_key)

        # Download the file
        file_type_and_name = s3_manager.download_file(file_key, temp_file_path)

        # Run Semgrep
        self.run_semgrep_on_file(temp_file_path, file_type_and_name[0], file_type_and_name[1])

    # ----------------------- SEMGREP -------------------------------
    def run_semgrep_on_file(self, temp_file_path, file_type, file_name):
        """Run Semgrep on the file and save the output to a specified path."""
        if file_type == 0: # JS
            filetype = '.js'
        elif file_type == 1: # External
            filetype = 'external'
        elif file_type == 2: # Inline
            filetype = 'inline'
        log_print(f"Running Semgrep on file: URL = {file_name}, filetype = {filetype}, temp_file_path = {temp_file_path}")

        try:
            # Run the Semgrep command and capture the output and errors
            result = subprocess.run(
                ['semgrep', temp_file_path, '--config', self.rules, '--no-git-ignore'],
                text=True,  # make stdout and stderr both strings
                capture_output=True  # Capture stdout and stderr
            )

            # Write the output to the file ONLY if it finds any semgrep matches
            if result.stdout:
                log_print("SEMGREP MATCH FOUND!")

                # make vuln dir
                vuln_dir = os.path.join(OUTPUT_PATH, get_domain(file_name), hashlib.sha256((temp_file_path).encode()).hexdigest())
                os.makedirs(vuln_dir, exist_ok=True)

                self.vuln_count += 1
                text_path = os.path.join(vuln_dir, "result.txt")

                # Write the semgrep output to the result.txt
                with open(text_path, 'w') as output_file:
                    # Write the file type and URL
                    output_file.write(f"Filetype is: {filetype}")
                    output_file.write(f"\nURL: {file_name}\n")

                    # Write the stdout and stderr - this contains the semgrep output
                    output_file.write(result.stdout)
                    if result.stderr:
                        output_file.write("\nstderr:\n")
                        output_file.write(result.stderr)

                # Move the temp file into the vuln_dir
                shutil.move(temp_file_path, os.path.join(vuln_dir, os.path.basename(temp_file_path)))
            else:
                # Delete the temp file
                os.remove(temp_file_path)

        except Exception as e:
            # Log any exceptions that might occur during the subprocess execution
            log_print("An exception occurred: " + str(e))

# ------------------------------------------------------------------------------------------

def remove_https(domains):
    cleaned = []
    for domain in domains:
        domain = domain.removeprefix("https://")
        domain = domain.removeprefix("http://")
        cleaned.append(domain)
    return cleaned


def get_domain(url):
    url = url.split(" ")[0] # To handle external URLs, which have " - external URL: ..." after
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def parse_args():
    parser = argparse.ArgumentParser(description="S3 JS File Processor")
    parser.add_argument('--search', '-s', nargs='+', help='Filter files by prefixes (e.g. example.com sub.example.com example.com/|www/|||/inline.js)')
    parser.add_argument('--rules', help='Path to Semgrep rule file or directory')
    parser.add_argument('--s3', '-s3', action='store_true', help='If you want to connect with an S3 bucket. See ../storage')
    parser.add_argument('--noexternal', '-noex', action='store_true', help="For running locally, if you don't want to fetch external files")
    parser.add_argument('--nohakrawler', '-nohak', action='store_true', help="For running locally, if you don't want to run hakrawler first on the domains.")
    return parser.parse_args()

def main():
    log_print("Command: " + ' '.join(sys.argv))
    # Fetch command line parameters
    args = parse_args()

    if args.s3 and (args.noexternal or args.nohakrawler):
        log_print("ERROR: -noex and -nohak are only for running locally (without -s3).")
        sys.exit(1)

    rules = args.rules

    # if -s is a .txt file, fetch the URLs from there
    if args.search and len(args.search) == 1 and args.search[0].endswith('.txt'):
        file_path = args.search[0]
        if not os.path.isfile(args.search[0]):
            print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
            sys.exit(1)
        with open(file_path, 'r') as f:
            search = [line.strip() for line in f if line.strip()]
    else:
        search = args.search

    # Create the API
    semgrepAPI = SemgrepAPI(rules, search)

    if args.s3:
        semgrepAPI.run_all_from_bucket()
    else: # Running locally
        # IF hakrawler flag:
        if not args.nohakrawler:
            semgrepAPI.run_hakrawler_all()

        semgrepAPI.run_all_local(args.noexternal)

    if semgrepAPI.vuln_count == 1:
        log_print(f"Finished. {semgrepAPI.vuln_count} vulnerability found. Check {OUTPUT_PATH}")
    else:
        log_print(f"Finished. {semgrepAPI.vuln_count} vulnerabilities found. Check {OUTPUT_PATH}")

if __name__ == "__main__":
    main()