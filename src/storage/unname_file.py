JS_FILE = 0
EXTERNAL = 1
INLINE = 2


def unname_js(path):
    return path_to_url(path)

# Converts a path to a specific url and includes type
# 0 - standard js file
# 1 - external js file
# 2 - inline js
def path_to_url(path):
    if "/||/" in path:
        parts = path.split("/||/")
        main_url = path_to_url_helper(parts[0])
        external_url = path_to_url_helper(parts[1])
        return [EXTERNAL, main_url + " - external URL: " + external_url]

    if "/|||/" in path:
        parts = path.split("/|||/")
        main_url = path_to_url_helper(parts[0])
        return [INLINE, main_url]

    return [JS_FILE, path_to_url_helper(path)]

# Helper function for path_to_url that reconstructs the url (default to https)
def path_to_url_helper(path):
    parts = path.split('/')
    domain_string = parts[0]

    subdomains = []
    path_index = 1
    for i in range(1, len(parts)):
        if parts[i].startswith('|'):
            subdomains.append(parts[i][1:])
            path_index += 1
        else:
            path_index = i
            break

    subdomains = reversed(subdomains)
    subdomain_string = "".join([subdomain + "." for subdomain in subdomains])
    url_path_string = "".join(["/" + item for item in parts[path_index:] if item])

    return "https://" + subdomain_string + domain_string + url_path_string