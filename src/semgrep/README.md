# Semgrep

# Purpose

This folder is an API for calling semgrep on the files.

The analyze_prefix_search.py file should be implemented to take a prefix search as input

- ex. 'https://google.com/|docs/|help/spreadsheets'

and should fetch all files that fit that prefix (using the storage directory) and run semgrep on them.


report_generator can be used to analyze all the output from the prefix search