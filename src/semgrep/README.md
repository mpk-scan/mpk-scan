# Semgrep API

# Purpose

This directory is an API for calling semgrep on the files.

TODO: The semgrep.py file should be implemented to take a prefix search as input

- ex. 'https://google.com/|docs/|help/spreadsheets'

and should fetch all files that fit that prefix (using the storage directory) and run semgrep on them.

# Local Configuration

Running semgrep on every file in the bucket

1. Set up a venv:

`python3 - venv myenv`
`source myenv/bin/activate`

2. In the venv, `pip install -r requirements.txt`
- should install boto3 and semgrep

3. From src, run `python3 -m semgrep.semgrep`
- this just runs the semgrep/semgrep.py file

# Sources

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html#creating-paginators