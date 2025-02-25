# Sp25Capstone Group 8

# Overview
This project aims to combine web scraping for client-side Javascript files with Semgrep, an open-source static code vulnerability scanner.

# Workflow
There are 2 main phases of the workflow.

1. Web crawler/scraper
   - Find valid URLs
   - Upload all JS from the URLs (both inline and external JS files) to storage (S3 bucket)
  
3. Semgrep
  - Take a prefix search as input (https://help.docs.google.com/spreadsheets/) and run [https://semgrep.dev/](semgrep)
  - Use proprietary and default Semgrep rules (in .yaml files) to configure Semgrep to catch vulnerabilities in minified Javascript
  - Output results, sorted by severity

# Functionality
The desired functionality will have the web crawler running indefinitely to fill up the S3 bucket with JS from the web.
The semgrep can run as needed (and through a web app) to scan JS and output vulnerabilities wherever needed.
