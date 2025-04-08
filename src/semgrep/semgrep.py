import sys
import os
import subprocess
from datetime import datetime
import argparse
import jsbeautifier

# ------------------------------------------------------------------------------------------

OUTPUT_DIR = 'output/logs'

CURRENT_TIME = datetime.now().strftime("%Y%m%d-%H%M%S")

OUTPUT_PATH = os.path.join(OUTPUT_DIR, CURRENT_TIME)
os.makedirs(OUTPUT_PATH, exist_ok=True)

LOG_FILE = os.path.join(OUTPUT_PATH, 'log.txt')

DEFAULT_RULES_DIRECTORY = "production_rules"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = os.path.join(SCRIPT_DIR, "..", "storage")
sys.path.append(os.path.abspath(STORAGE_PATH))

from s3_manager import S3Manager

# ------------------------------------------------------------------------------------------

def log_print(message):
    """Append a log message to the log file in the timestamped directory."""
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)

class SemgrepAPI:

    def __init__(self, rules, domains):
        # Attributes
        self.domains = domains

        if rules == None:
            self.rules = DEFAULT_RULES_DIRECTORY
        else:
            self.rules = rules

        log_print('Running with domains: ' + str(self.domains))
        log_print('Running with rules: ' + str(self.rules))

    def run_semgrep_on_file(self, file_path, output_path, file_type_and_name):
        """Run Semgrep on the file and save the output to a specified path."""
        try:
            # Run the Semgrep command and capture the output and errors
            result = subprocess.run(
                ['semgrep', file_path, '--config', self.rules, '--no-git-ignore'],
                text=True,  # make stdout and stderr both strings
                capture_output=True  # Capture stdout and stderr
            )

            # Write the output to the file ONLY if it finds any semgrep matches
            if result.stdout:
                with open(output_path, 'w') as output_file:
                    # Write the file type and URL
                    if file_type_and_name[0] == 0: # JS
                        filetype = '.js'
                    elif file_type_and_name[0] == 1: # External
                        filetype = 'external'
                    elif file_type_and_name[0] == 2: # Inline
                        filetype = 'inline'
                    output_file.write(f"Filetype is: {filetype}")
                    output_file.write(f"\nURL: {file_type_and_name[1]}\n")

                    # Write the stdout and stderr - this contains the semgrep output
                    # print("############################res#######################")
                    # print(result.stdout)
                    # print("############################res#######################")
                    # output_file.write(result.stdout)
                    # self._beautify_and_rerun(file_path, output_file)
                    if result.stderr:
                        output_file.write("\nstderr:\n")
                        output_file.write(result.stderr)

        except Exception as e:
            # Log any exceptions that might occur during the subprocess execution
            log_print("An exception occurred: " + str(e))

    # def _beautify_and_rerun(self, file_path, output_file):
    #     """Beautify JavaScript code and re-run Semgrep."""
    #     try:
    #         with open(file_path, 'r') as f:
    #             original_code = f.read()

    #         beautified_code = jsbeautifier.beautify(original_code)

    #         #creating the beautified code somewhere temporarily
    #         temp_path = file_path + ".beautified.js"
    #         with open(temp_path, 'w') as temp_file:
    #             temp_file.write(beautified_code)

    #         result = subprocess.run(
    #             ['semgrep', temp_path, '--config', self.rules, '--no-git-ignore'],
    #             text=True,
    #             capture_output=True
    #         )

    #         output_file.write(result.stdout)
            
    #         if result.stderr:
    #             output_file.write("\nBeautified stderr:\n")
    #             output_file.write(result.stderr)

    #     except Exception as e:
    #         output_file.write("\nBeautification error " + str(e))
            
    #     finally:
    #         if os.path.exists(temp_path):
    #             os.remove(temp_path)

    def run_all(self):
        """Run Semgrep on all the files"""
        s3_manager = S3Manager()

        if not self.domains:
            file_list = s3_manager.list_files()
        else:
            file_list = s3_manager.list_files_filtered(self.domains)

        log_print("Fetched filenames from the S3 bucket. Running...")

        for file_key in file_list:

            hash_file_key = str(hash(file_key)) + '.js'

            log_print("Running on file: " + str(file_key) + ' - temporary hash name' + hash_file_key)

            # Temporary file path
            temp_file_path = os.path.join('/tmp', hash_file_key)
            
            # Download the file
            file_type_and_name = s3_manager.download_file(file_key, temp_file_path)
            
            # Run Semgrep and output the results to the specified output directory
            output_file_path = os.path.join(OUTPUT_PATH, f"{os.path.basename(hash_file_key)}_result.txt")
            self.run_semgrep_on_file(temp_file_path, output_file_path, file_type_and_name)
            
            # Delete the temporary file
            os.remove(temp_file_path)

            # log_print(f"Semgrep complete for file: {file_key}")

# ------------------------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="S3 JS File Processor")
    parser.add_argument('--domains', nargs='+', help='Filter files by domain prefixes (e.g. example.com sub.example.com)')
    parser.add_argument('--rules', help='Path to Semgrep rule file or directory')
    return parser.parse_args()

def main():
    # Fetch command line parameters
    args = parse_args()
    domains = args.domains
    rules = args.rules

    # Create the API
    semgrepAPI = SemgrepAPI(rules, domains)

    semgrepAPI.run_all()

if __name__ == "__main__":
    main()
