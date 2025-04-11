# Semgrep API

# Configuration

Running semgrep on every file in the bucket

1. Set up a venv in this repo's root directory:

`python3 -m venv myenv`
`source myenv/bin/activate`

2. In the venv, `pip install -r requirements.txt`
- should install boto3 and semgrep

3. If needed, configure environment variables with:

`export AWS_ACCESS_KEY_ID=`
`export AWS_SECRET_ACCESS_KEY=`

# Usage

Run semgrep on files in the bucket with:

`python3 semgrep.py` optional flags: `--domains example.com sub.test.com ...` `--rules production_rules/proprietary/`

# Sample output for semgrep.py:

- Log files go to: output/log/[TIME]/log.txt

sample `log.txt` file:

```
2025-04-03 00:27:44 - Running with domains: ['amazon.com', 'reddit.com']
2025-04-03 00:27:44 - Running with rules: production_rules/proprietary/
2025-04-03 00:27:46 - Fetched filenames from the S3 bucket. Running...
2025-04-03 00:27:46 - Running on file: amazon.com.au/|sell/|||/inline.js - temporary hash name-7559768333442326107.js
2025-04-03 00:27:48 - Running on file: amazon.com.br/|venda/|||/inline.js - temporary hash name-8194479248224545517.js
2025-04-03 00:27:51 - Running on file: amazon.com.mx/|vender/|||/inline.js - temporary hash name7778720338677084361.js
```

- Any semgrep findings will be logged to a separate file called:

output/log/[TIME]/[TEMP_FILE_HASH].js_result.txt



# Sources

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html#creating-paginators