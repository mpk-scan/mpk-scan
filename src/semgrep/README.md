# Semgrep API

# Purpose

This directory is an API for calling semgrep on the files.

TODO: The semgrep.py file should be implemented to take a prefix search as input

- ex. 'https://google.com/|docs/|help/spreadsheets'

and should fetch all files that fit that prefix (using the storage directory) and run semgrep on them.

# Sources

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/paginators.html#creating-paginators