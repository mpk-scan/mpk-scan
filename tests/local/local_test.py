import subprocess
import sys
import os
import jsbeautifier
import requests
import concurrent.futures
from urllib.parse import urljoin, urlparse
# Go two directories up (from tests/local/) to the root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Append crawler and storage folders to sys.path
sys.path.append(os.path.join(ROOT_DIR, "src", "crawler"))
sys.path.append(os.path.join(ROOT_DIR, "src", "storage"))
from html_parser import extract_javascript
import argparse
from datetime import datetime

# ------------------------------------------------------------------------------------------

# Output directory

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'local_test_output')
OUTPUT = 'local_test_output'
CURRENT_TIME = datetime.now().strftime("%Y%m%d-%H%M%S")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, CURRENT_TIME)
os.makedirs(OUTPUT_PATH, exist_ok=True)

FINDINGS_DIR = "local_findings"
os.makedirs(FINDINGS_DIR, exist_ok=True)

# Logging

LOG_FILE = os.path.join(OUTPUT_PATH, 'log.txt')

from name_file import name_js, name_with_external, name_inline

# Temp directory

TEMP_DIR = "local_tmp"

os.makedirs(TEMP_DIR, exist_ok=True)

session = requests.Session()

# Initialize variables
DEFAULT_RULES_DIRECTORY = "../../src/semgrep/production_rules"

files = []


# ------------------------------------------------------------------------------------------

def log_print(message):
    """Append a log message to the log file in the timestamped directory."""
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

class MPK_Scan:
    def __init__(self, domains, rules):
        if rules == None:
            self.rules = DEFAULT_RULES_DIRECTORY
        else:
            if os.path.exists(rules):
                self.rules = rules
            else:
                log_print('The path provided does not exist: ' + str(rules))

        self.external_files = []

    def run_hakrawler(self,domain):
        """Runs Hakrawler with subdomain exploration enabled."""
        log_print(f"Running Hakrawler on {domain}")

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

    def process_url(self,url, no_external=False):
        '''For a given url, extract all js associated with it (inline and external)'''
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
            temp_filename = str(hash(url))
            self.save_js_file(temp_filename, response.text, name_js(url))
            
        # If url is other
        elif 'text/html' in content_type:
            inline_js, external_js_links = extract_javascript(url, response.text)
            # Fetch inline JS
            if inline_js:
                temp_filename = str(hash(url)) + ".js"
                self.save_js_file(temp_filename, inline_js, name_inline(url))
            
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
                            temp_filename = str(hash(url+external_url)) + ".js"
                            self.save_js_file(temp_filename, response.text, name_with_external(url, external_url))


    # Save temp file
    def save_js_file(self,temp_name, content, filename):   
        filepath = os.path.join(TEMP_DIR, temp_name)
        beautified_code = jsbeautifier.beautify(content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(beautified_code)

        self.run_semgrep_on_file(filepath)

    def run_semgrep_on_file(self, filepath):
        try:
            if os.path.isfile(filepath):
                log_print(f'Running semgrep on the file: {filepath}')

                result = subprocess.run(
                ['semgrep', '--config', self.rules, '--no-git-ignore', filepath],
                text=True,
                capture_output=True
                )
                
                # Write the output to the file ONLY if it finds any semgrep matches
                if result.stdout:
                    # Copy the file with findings into local_findings/
                    log_print('Semgrep Complete: FINDING!!!')
                    findings_path = os.path.join(FINDINGS_DIR, os.path.basename(filepath))
                    with open(findings_path, "w", encoding="utf-8") as f_out:
                        with open(filepath, "r", encoding="utf-8") as f_in:
                            f_out.write(f_in.read())

                    # Save the semgrep output as well
                    output_file_path = os.path.join(FINDINGS_DIR, f"{os.path.basename(filepath)}.semgrep.txt")
                    with open(output_file_path, "w") as output_file:
                        output_file.write(result.stdout)
                        if result.stderr:
                            output_file.write("\n[stderr]:\n")
                            output_file.write(result.stderr)
                else: 
                    log_print('Semgrep Complete: No findings.')
                    os.remove(filepath)
        except Exception as e:
            # Log any exceptions that might occur during the subprocess execution
            log_print("An exception occurred: " + str(e))

# ---------------------End of Class MPK_Scan----------------------------------------------------------------------------------------------------------- #

def parse_args():
    parser = argparse.ArgumentParser(description="Run Hakrawler and extract JS files from URLs.")
    parser.add_argument('--domains', nargs='+', help='Filter files by domain prefixes (e.g. example.com sub.example.com)')
    parser.add_argument(
        "--no-external", "-noex",
        action="store_true",
        help="If set, do NOT fetch or process external JavaScript files"
    )
    parser.add_argument('--rules', help='Path to Semgrep rule file or directory')

    return parser.parse_args()


def main():
    args = parse_args()
    domains = args.domains
    rules = args.rules
    
    mpk = MPK_Scan(domains, rules)

    urls = [] # For printing hackrawler output, for local use
    for domain in domains:
        mpk.external_files = []
        urls = mpk.run_hakrawler(domain)
        # Process URLs in parallel (Change workers if needed)
        log_print(f"Processing {len(urls)} URLs from {domain}")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(mpk.process_url, url, no_external=args.no_external) for url in urls]
            for future in concurrent.futures.as_completed(futures):
                future.result()


if __name__ == "__main__":
    main()
