import tldextract
from urllib.parse import urlparse

# Function to get insertion path
def name_js(url):
    return url_to_path(url)

# Function to get insertion external js path
def name_with_external(url, external):
    main_url = url_to_path(url)
    external_url = url_to_path(external)
    return add_external(main_url, external_url)

# Function to get insertion inline js path
def name_inline(url):
    main_url = url_to_path(url)
    return add_inline(main_url)

# Converts url to custom path for s3 storage
def url_to_path(url):
    parsed_url = urlparse(url if "://" in url else "http://" + url)
    domains = tldextract.extract(parsed_url.netloc)
    domain = domains.domain + "." + domains.suffix
    subdomains = list(reversed(domains.subdomain.split('.')))

    subdomain_string = ""
    if subdomains != ['']:
        for subdomain in subdomains:
            subdomain_string += "/|" + subdomain

    url_path = parsed_url.path
    path = domain + subdomain_string + url_path
    return path

# Adds external url to path
def add_external(path, external_path):
    return path + "/||/" + external_path

# Marks path as inline js
def add_inline(path):
    return path + "/|||/inline.js"