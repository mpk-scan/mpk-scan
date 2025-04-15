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

# Sample output for semgrep.py:

- Log files go to: output/log/[TIME]/log.txt

sample `log.txt` file:

```
2025-04-15 13:39:01 - Using prefix search on: ['example.com/|www/|||/inline.js', 'meta.com/|www/|||/inline.js']
2025-04-15 13:39:01 - Running with rules: production_rules
2025-04-15 13:39:07 - Fetched filenames from the S3 bucket. Running...
2025-04-15 13:39:07 - Running on file: meta.com/|www/|||/inline.js - temporary hash namedaf708377b6e68670a56cf265f4f76a678ba3054b751132b130ed76ebdae8f82.js
2025-04-15 13:39:10 - Finished.
```

- Any semgrep findings will be logged to a separate file called:

output/log/[TIME]/[TEMP_FILE_HASH].js_result.txt


# Sources

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html#creating-paginators