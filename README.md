# Sp25Capstone Group 8

# Overview
This project aims to combine web scraping for client-side Javascript files with Semgrep, an open-source static code vulnerability scanner.

# Purpose
The desired functionality will have the web crawler running indefinitely to fill up the S3 bucket with JS from the web.
The semgrep can run as needed (and through a web app) to scan JS and output vulnerabilities wherever needed.

# Functionality

1. `/crawler` - Web crawler/scraper
   - Find valid URLs
   - Upload all JS from the URLs (both inline and external JS files) to storage (S3 bucket)
  
3. `/semgrep` - Semgrep API
  - Runs Semgrep (with the custom ruleset) on the files in the bucket
  - Log results
