# Semgrep API

# Configuration

Running semgrep on every file in the bucket

1. Set up a venv in this repo's root directory:

`python3 -m venv myenv`
`source myenv/bin/activate`

2. In the venv, `pip install -r requirements.txt`

3. If needed, configure environment variables with:

`export AWS_ACCESS_KEY_ID=`
`export AWS_SECRET_ACCESS_KEY=`

# Usage

Run semgrep on files in the bucket with:

`python3 semgrep.py` optional flags: `--search example.com sub.test.com example.com/|www/|||/inline.js ...` `--rules production_rules/proprietary/`

You can also pass a list of domains as a text file with --search

`python3 semgrep.py -s priority_urls.txt`

# Sample output for semgrep.py:

- Log files go to: output/log/[TIME]/log.txt

sample `log.txt` file:

```
2025-04-15 17:47:58 - Using prefix search on: ['test.com, example.com/']
2025-04-15 17:47:58 - Running with rules: production_rules
2025-04-15 17:48:04 - Fetched filenames from the S3 bucket. Running...
2025-04-15 17:48:04 - Running on file: <redacted>.com/|advertising/register/||/<redacted>.net/|<redacted>/assets-1.js - temporary hash name 477567ff9bbfbeb97bf710d0013cfab4b54029feb6356e07e975d3acfa3f9dd3.js
2025-04-15 17:48:11 - Finished. 1 vulnerability found. Check output/logs/20250415-174758
```

- Any semgrep findings will be logged to a separate file called:

output/log/[TIME]/[TEMP_FILE_HASH].js_result.txt


# Sources

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html#creating-paginators