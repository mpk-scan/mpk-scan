from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def extract_javascript(base_url, html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract inline JS
    inline_scripts = [script.get_text() for script in soup.find_all("script") if not script.has_attr("src")]
    inline_js = "\n".join(inline_scripts)
    
    # Extract external JS links
    external_js_links = [script["src"] for script in soup.find_all("script", src=True)]
    
    return inline_js, external_js_links
