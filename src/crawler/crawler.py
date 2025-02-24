import requests
import os
from urllib.parse import urljoin, urlparse
from html_parser import extract_javascript
# from s3_uploader import upload_to_s3  # Commented out for testing

def fetch_url_content(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}: {response.status_code}")
        return
    
    content_type = response.headers.get('Content-Type', '')
    if url.endswith('.js') or 'javascript' in content_type:
        filename = os.path.basename(urlparse(url).path)
        print(f"--- JS File: {filename} ---")
        print(response.text)
        print("--- End of Js File ---\n")
        # upload_to_s3(filename, response.text)  # Commented out for testing leverage this api
    elif 'text/html' in content_type:
        inline_js, external_js_links = extract_javascript(url, response.text)
        
        # Print inline JS
        if inline_js:
            print(f"--- Inline JavaScript from {url} ---")
            print(inline_js)
            print("--- End of Inline JavaScript ---\n")
            # inline_filename = f"{urlparse(url).netloc}_inline.js"
            # upload_to_s3(inline_filename, inline_js)  # Commented out for testing
        
        # Fetch and print external JS
        for js_url in external_js_links:
            absolute_js_url = urljoin(url, js_url)  # Resolve relative URLs
            fetch_url_content(absolute_js_url)  # Recursive call for JS files

if __name__ == "__main__":
    # testing with the w3 schools doma
    test_url = "https://www.w3schools.com/js/default.asp"
    fetch_url_content(test_url)