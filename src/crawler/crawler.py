import subprocess
import sys
import os
import requests
import concurrent.futures
from urllib.parse import urljoin, urlparse
from html_parser import extract_javascript

sys.path.append(os.path.abspath("../storage"))

from insert_file import insert_js, insert_with_external, insert_inline

# Configuration
OUTPUT_DIR = "hackrawler_output"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()

files = []

external_files = []


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
        line.strip()
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
        # 4 lines below for local use
        filename = sanitize_filename("REGULAR", url)
        save_js_file(filename, response.text)
        files.append(insert_js(url))
        # s3_filename = insert_js(url)
        # upload_to_s3(s3_filename, response.text)  # Commented out for testing leverage this api

    # If url is other
    elif 'text/html' in content_type:
        inline_js, external_js_links = extract_javascript(url, response.text)
        # Fetch inline JS
        if inline_js:
            # 3 lines below for local use
            filename = sanitize_filename("INLINE", url)
            save_js_file(filename, inline_js)
            files.append(insert_inline(url))
            # s3_inline_filename = insert_inline(url)
            # upload_to_s3(s3_inline_filename, inline_js)  # Commented out for testing
        
        # Fetch external JS
        for js_url in external_js_links:

                external_url = urljoin(url, js_url)  # Resolve relative URLs
                if external_url not in external_files:
                    response = requests.get(external_url)
                    if response.status_code != 200:
                        print(f"Failed to fetch {url}: {response.status_code}")
                        return  
                    content_type = response.headers.get('Content-Type', '')
                    if external_url.endswith('.js') or 'javascript' in content_type:
                        external_files.append(external_url)
                        # 3 lines below for local use
                        files.append(["EXTERNAL" ,insert_with_external(url, external_url),url ,external_url])
                        full_filename = sanitize_filename("EXTERNAL", url, external_url)
                        save_js_file(full_filename, response.text)
                        # s3_external_filename = insert_with_external(url, external_url)
                        # upload_to_s3(s3_external_filename, inline_js)  # Commented out for testing

# For debuging and local testing
def save_js_file(filename, content):   
    print(f"Saving JS file: {filename}")
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# For debuging and local testing
def sanitize_filename(prefix, base_url, extra_url=None):
    def get_safe_parts(url):
        parsed = urlparse(url)
        scheme = parsed.scheme or 'http'
        netloc = parsed.netloc or 'nohost'
        path = parsed.path.strip('/').replace('/', '_') or 'root'
        return f"{scheme}_{netloc}_{path}"
    
    filename = f"{prefix}___{get_safe_parts(base_url)}"
    
    if extra_url:
        filename += f"____{get_safe_parts(extra_url)}"

    return filename



def main():
    target_domains = [
        "https://demo.testfire.net/"
    ]

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
