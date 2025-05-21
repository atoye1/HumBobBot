import os
from dotenv import load_dotenv

load_dotenv()

# General
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# DietCrawler
DIET_CRAWLER_MAIN_URL = "https://btcep.humetro.busan.kr"
DIET_CRAWLER_MENU_URL = "https://btcep.humetro.busan.kr/portal/default/main/eboard/eMenu"
DIET_UPLOAD_ENDPOINT = "http://130.162.153.197:8000/diet/upload"
BTCEP_ID = os.getenv("BTCEP_ID")
BTCEP_PW = os.getenv("BTCEP_PW")

# RegulationCrawler
REGULATION_CRAWLER_BASE_URL = "http://www.humetro.busan.kr"
# For now, target_boards will remain in RegulationCrawler.py as it's complex and might be stable.
DOWNLOAD_DIR = os.path.join(BASE_DIR, "miscs") # For downloaded HWP/PDFs
REGULATION_HTML_DIR = os.path.join(ASSETS_DIR, "html", "_regulation") # For converted HTMLs by RegulationCrawler

# Server
RULES_JSON_PATH = os.path.join(BASE_DIR, "rules.json")
SERVER_IMAGE_ASSETS_PATH = os.path.join(ASSETS_DIR, "image")
# This path is used by the server to serve statically, potentially different from where RegulationCrawler writes.
SERVER_REGULATION_ASSETS_PATH = os.path.join(ASSETS_DIR, "html", "_regulation")

# Ensure all paths are absolute or correctly relative to the project structure.
# Example: print(f"Base directory: {BASE_DIR}")
# print(f"Assets directory: {ASSETS_DIR}")
# print(f"Regulation HTML directory (Crawler output): {REGULATION_HTML_DIR}")
# print(f"Server Regulation HTML directory (Static serve): {SERVER_REGULATION_ASSETS_PATH}")
# print(f"Download directory: {DOWNLOAD_DIR}")
# print(f"Rules JSON path: {RULES_JSON_PATH}")

# Logging Configuration
import logging
import sys

LOGGING_LEVEL = logging.INFO # Or from env var
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(lineno)d - %(message)s"
LOG_FILE = os.path.join(BASE_DIR, "app.log") # Store app.log in the base directory

# Ensure the log directory exists if LOG_FILE includes a subdirectory
# For now, it's in BASE_DIR, so no extra directory creation is needed for the file itself.

logging.basicConfig(
    level=LOGGING_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout) # To see logs in console
    ]
)

# Example of getting a logger instance in other files:
# import logging
# logger = logging.getLogger(__name__)

# File Processing
KEEP_DOWNLOADED_ORIGINALS = False # Set to True to keep original HWP/PDFs after HTML conversion
