import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath("../src/storage"))

from s3_manager import S3Manager
from unname_file import unname_js

CURRENT_TIME = datetime.now().strftime("%Y%m%d-%H%M%S")

s3 = S3Manager()

file = 'spotify.com/|artists/||/spotifycdn.com/|mrkt/artists-spotify-com/_next/static/chunks/framework-ab1cb6e85256eca1.js'

fileplace = 'output/test_' + CURRENT_TIME

# if '|' in file:
#     file = unname_js(file)[1]

s3.download_file(file, fileplace)

print(f"{file} downloaded to {fileplace}")
