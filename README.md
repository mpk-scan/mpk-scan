# mpk-scan - Web JS Vulnerability Scanner
CLI to scrape front-end JavaScript files from websites and scan them for security vulnerabilities using Semgrep rules to detect malicious code patterns.

Supports optional S3 bucket integration.

# Installation

`git clone https://github.com/mpk-scan/mpk-scan.git`

1. Set up a venv in root:

`python3 -m venv myenv`
`source myenv/bin/activate`

2. In the venv, `pip install -r requirements.txt`

3. To integrate with S3, configure environment variables:

`AWS_ACCESS_KEY_ID`
`AWS_SECRET_ACCESS_KEY`

and update constructor in s3_manager.py in `~/src/storage`.

# Requirements
1. Python 3.7 or higher
2. (reccomended) Hakrawler
- `hakrawler` must be installed and added to the system's PATH.  
  With Go installed, you can install `hakrawler` using the following command:
  ```bash
  go install github.com/hakluke/hakrawler@latest
- ensure the Go bin directory is in your PATH
  ```bash
  export PATH=$PATH:$(go env GOPATH)/bin

You may use --nohak to run without hakrawler

# Usage
See /mpkscan for usage.

1. `/mpkscan` (reccomended) - Webcrawler + vuln scanner
   - Full functionality, allows optional s3 usage

3. `/crawler` - Web crawler/scraper
   - Exclusively scraping with hakrawler to fill up S3 bucket
