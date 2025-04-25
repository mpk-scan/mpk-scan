# mpk-scan
A command-line tool to scrape front-end JavaScript files from websites and scan them for security vulnerabilities using Semgrep rules to detect malicious code patterns.
Supports optional S3 bucket integration.

# Requirements
1. Python 3.7 or higher
2. Hakrawler
- `hakrawler` must be installed and added to the system's PATH.  
  You can install `hakrawler` using the following command:
  ```bash
  go install github.com/hakluke/hakrawler@latest
- ensure the Go bin directory is in your PATH
  ```bash
  export PATH=$PATH:$(go env GOPATH)/bin

# Usage
See /mpkscan for usage.

1. `/mpkscan` (reccomended) - Webcrawler + vuln scanner
   - Full functionality, allows optional s3 usage

3. `/crawler` - Web crawler/scraper
   - Exclusively for s3 bucket integration
