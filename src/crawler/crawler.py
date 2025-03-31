import subprocess
import sys
import os
import requests
import concurrent.futures
from urllib.parse import urljoin, urlparse
from html_parser import extract_javascript

sys.path.append(os.path.abspath("../storage"))

from name_file import name_js, name_with_external, name_inline

from s3_manager import S3Manager

# Configuration
OUTPUT_DIR = "temp"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()

files = []

external_files = []

s3 = S3Manager()

def run_hakrawler(domain):
    """Runs Hakrawler with subdomain exploration enabled."""
    print(f"Running Hakrawler on {domain}")

    result = subprocess.run(
        ["hakrawler", "-subs"],
        input=domain,
        capture_output=True,
        text=True
    )

    urls = {
        line.strip().rstrip('/')
        for line in result.stdout.splitlines()
        if line.strip().startswith(("http://", "https://"))
    }

    print(f"Discovered {len(urls)} URLs")
    return urls

def process_url(url):
    '''For a given url, extract all js associated with it (inline and external)'''

    response = session.get(url, timeout=5)
    if response.status_code != 200:
        print(f"Failed to fetch {url}: {response.status_code}")
        return
    content_type = response.headers.get('Content-Type', '')

    #If url is a js file
    if url.endswith('.js') or 'javascript' in content_type:
        temp_filename = str(hash(url))
        save_js_file(temp_filename, response.text, name_js(url))
        
    # If url is other
    elif 'text/html' in content_type:
        inline_js, external_js_links = extract_javascript(url, response.text)
        # Fetch inline JS
        if inline_js:
            temp_filename = str(hash(url)) 
            save_js_file(temp_filename, inline_js, name_inline(url))
        
        # Fetch external JS
        for js_url in external_js_links:
                external_url = urljoin(url, js_url)  # Resolve relative URLs

                # Check for duplicate external
                if external_url not in external_files:
                    response = requests.get(external_url)
                    if response.status_code != 200:
                        print(f"Failed to fetch {url}: {response.status_code}")
                        return  
                    content_type = response.headers.get('Content-Type', '')
                    if external_url.endswith('.js') or 'javascript' in content_type:
                        external_files.append(external_url)
                        temp_filename = str(hash(url+external_url))
                        save_js_file(temp_filename, response.text, name_with_external(url, external_url))


# Save temp file and upload to s3
def save_js_file(temp_name, content, filename):   
    print(f"Saving JS file: {temp_name}")
    filepath = os.path.join(OUTPUT_DIR, temp_name)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    s3.upload_file(filepath, filename)
    os.remove(filepath)


def main():
   
    with open("urls.txt", "r") as f:
        lines = f.readlines()

    target_domains = [line.strip() for line in lines]

    print(target_domains)
    
    urls = [] # For printing hackrawler output, for local use
    for domain in target_domains:
        external_files = []
        urls = run_hakrawler(domain)
        print(f"Processing: {domain}")
        # Process URLs in parallel (Change workers if needed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(process_url, urls)

    # For debuging and local testing (Use 1 domain)
    with open("output.txt", "w", encoding="utf-8") as f:
        for item in files:
            f.write(f"{item}\n")
    with open("hakrawler.txt", "w", encoding="utf-8") as f:
        for item in urls:
            f.write(f"{item}\n")


if __name__ == "__main__":
    main()
