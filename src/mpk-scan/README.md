# mpk-scan

# Configuration

1. Set up a venv in root:

`python3 -m venv myenv`
`source myenv/bin/activate`

2. In the venv, `pip install -r requirements.txt`

3. To integrate with S3, configure environment variables for:

`AWS_ACCESS_KEY_ID`
`AWS_SECRET_ACCESS_KEY`

AND update \__init__ in s3_manager.py in `~/src/storage`

# Local Usage

`python3 mpk-scan.py`

Flags:
- search: `-s https://github.com https://example.com` or `-s urls.txt`, The domains to search
- nohak: `-nohak`, Does not use hakrawler on domains (only processes the URL and pulls external files and inline JS)
- noex: `-noex`, Doesn't fetch external JavaScript files (for hakrawler OR without hakrawler)
- rules: `-r`, Supply custom Semgrep rules (file OR directory)
- upload: `-u`, Uploads each JS file to the bucket before running Semgrep. See Configuration.

# Exclusive S3 usage

Does not crawl/scan files, only pulls them from the bucket.

`python3 mpk-scan.py -s3`

Flags:
- search: `-s https://github.com example.com example.com/|parent/|child example.com/||external.com` or `-s urls.txt`, The domains to search
- rules: `-r`, Supply custom Semgrep rules (file OR directory)

The flags -nohak, -noex, and -u are illogical and will throw an error if used with -s3.

# S3 Key naming system explained
For searching with -s3, any domains passed in with -s will be used as a prefix search in the S3 bucket.

`|` = a subdomain, any subsequent `|` are children of that subdomain. 

- `example.com/|parent/|child` = `child.parent.example.com`

`||` = Splits the URL into the original and external URLs (parsed from `<script src=...`).

- `example.com/||external.com/...`

`|||` = inline JavaScript of the URL.

- parsed `<script>...</script>`

# Output

A timestamped directory is created whenever mpk-scan.py runs with a log.txt file.

Any vulnerabilities found will be put into a dir in this timestamped directory, sorted by domain.

Each directory has the beautified JavaScript file (timestamped on when it was scraped), and the Semgrep stdout and stderr in a result.txt file.
