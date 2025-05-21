
import uvicorn
import json
import datetime
import logging
import sys

# Custom modules
import config

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from starlette.requests import Request
from starlette import status

from response_generator import generate_response, generate_rule_cards

from domain.diet import diet_router
from domain.regulation import regulation_router
from domain.ai import ai_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Humetro Bob Bot API", version="1.0.0")
startup_time = datetime.datetime.now()
logger.info("FastAPI application starting up...")

# load_dotenv() # Handled in config.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount('/image', StaticFiles(directory=config.SERVER_IMAGE_ASSETS_PATH), name='image')
logger.info(f"Mounted static directory for images at /image from {config.SERVER_IMAGE_ASSETS_PATH}")
app.mount('/regulation', StaticFiles(directory=config.SERVER_REGULATION_ASSETS_PATH), name='regulation')
logger.info(f"Mounted static directory for regulation HTMLs at /regulation from {config.SERVER_REGULATION_ASSETS_PATH}")

# --- Rules.json Loading and Usage ---
# `rules.json` (path configured via `config.RULES_JSON_PATH`) is loaded at server startup.
# This file serves as the primary data source for the `/get_rules` endpoint, which provides
# rule-based information to the user.
#
# Expected Structure of rules.json:
# The file must contain a JSON list of "rule" objects. Each object is expected to have at least:
#   - "title": (String) The official title or name of the rule/regulation. This field is crucial
#                as it's the primary field used for matching against user queries.
#   - "created_at": (String) The creation or last modification date of the rule document,
#                     typically in "YYYY-MM-DD" format. This information is used by
#                     `response_generator.generate_rule_cards`.
#   - "file_url": (String) A direct URL to the document file (e.g., HWP, PDF) associated
#                 with the rule. This URL is used in the response cards to link to the
#                 actual document.
#   - (Other fields, if any, might be present but are not directly used by the matching logic
#      in `/get_rules`, though they could be utilized by `generate_rule_cards`.)
#
# Example of a rule object in rules.json:
# {
#   "title": "관제운영규정 시행내규",
#   "created_at": "2023-09-12",
#   "file_url": "http://www.humetro.busan.kr/servlet/DownloadServlet?file_name=..."
# }
#
# Matching Logic in /get_rules Endpoint:
# 1. The user's raw message (`user_msg_raw`) is retrieved from the request.
# 2. Common keywords related to rules (e.g., '규정', '내규', '지침', '예규') are removed from the message.
# 3. The processed message is then split into individual words (tokens).
# 4. The system iterates through each token and then through each rule object in the loaded `rules` list.
# 5. A rule is considered a match if a token is found as a substring within the rule's "title" field
#    (e.g., if user says "관제운영규정", it matches the example title above).
#
# Response Format from /get_rules:
# - If one or more rules are matched, the endpoint returns a JSON response formatted as a
#   "basicCard" carousel. The `generate_rule_cards` function (from `response_generator.py`)
#   is responsible for creating these cards, using the information from the matched rule objects.
#   A maximum of 10 cards are returned.
# - If no rules match the user's query, a default "basicCard" is returned, indicating that
#   no relevant regulations were found.
# ---

rules = None
try:
    with open(config.RULES_JSON_PATH, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    logger.info(f"Successfully loaded rules from {config.RULES_JSON_PATH}")
except FileNotFoundError:
    logger.error(f"Rules file not found at {config.RULES_JSON_PATH}. /get_rules endpoint will not work correctly.")
    # rules remains None, which is handled in the endpoint
except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON from rules file {config.RULES_JSON_PATH}: {e}", exc_info=True)
    # rules remains None
except Exception as e:
    logger.error(f"An unexpected error occurred while loading rules from {config.RULES_JSON_PATH}: {e}", exc_info=True)
    # rules remains None


app.include_router(diet_router.router)
logger.info("Included diet_router.")
app.include_router(regulation_router.router)
logger.info("Included regulation_router.")
app.include_router(ai_router.router)
logger.info("Included ai_router.")

@app.get('/health', status_code=status.HTTP_200_OK)
def health():
    # This endpoint is usually for automated checks, extensive logging might be noisy.
    # logger.debug("Health check endpoint called.") 
    current_time = datetime.datetime.now()
    uptime = current_time - startup_time
    return {"msg": "server is up", "uptime":str(uptime)}


@app.post('/get_rules')
async def get_rules(request: Request):
    if rules is None:
        logger.error("Ruleset (rules.json) not loaded or failed to load, but /get_rules was called.")
        raise HTTPException(status_code=404, detail='No rules are loaded')

    try:
        body = await request.body()
        request_body = json.loads(body.decode()) # Can raise JSONDecodeError
        user_msg_raw = request_body.get('userRequest', {}).get('utterance') # Safer access
        
        if not user_msg_raw:
            logger.warning("Received /get_rules request with missing 'userRequest' or 'utterance'.")
            raise HTTPException(status_code=400, detail="Invalid request format: missing utterance.")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON body in /get_rules: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid JSON format.")
    
    logger.info(f"Received rule request for: '{user_msg_raw}'")
    
    # filter not worked due to namespace issue -> Fixed!!
    user_msg = user_msg_raw

    for word in ['규정', '내규', '지침', '예규']:
        user_msg = user_msg.replace(word, '')
    user_msg_words = user_msg.split()

    results = []
    for user_msg_word in user_msg_words:
        if not user_msg_word: # Skip empty strings after split
            continue
        for rule in rules: # Assumes rules is a list of dicts with 'title'
            if user_msg_word in rule.get('title', ''): # Safe access to rule['title']
                results.append(rule)
    
    if results:
        logger.info(f"Found {len(results)} matching rules for '{user_msg_raw}'. Returning top 10.")
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                       "carousel": {
                           "type": "basicCard",
                           "items": generate_rule_cards(request, results[:10]) # generate_rule_cards might also need logging/error handling
                       }
                    }
                ]
            }
        }
    else: # Explicitly handle no results case
        logger.info(f"No matching rules found for '{user_msg_raw}'.")
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                        {
                            "basicCard": {
                                "title": "관련 규정을 찾지 못했습니다.",
                                "description": f"입력한 메세지 : {user_msg_raw}",
                                "thumbnail": {
                                    "imageUrl": "https://user-images.githubusercontent.com/24848110/33519396-7e56363c-d79d-11e7-969b-09782f5ccbab.png",
                                },
                            }
                        }
                ]
            }
        }


if __name__ == "__main__":
    logger.info(f"Starting Uvicorn server on host 0.0.0.0, port 8000. LOG_LEVEL: {config.LOGGING_LEVEL}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None) # Set log_config=None to allow our basicConfig to rule
    except Exception as e:
        logger.critical(f"Failed to start Uvicorn server: {e}", exc_info=True)
        # Potentially exit if server fails to start
        sys.exit(1) # Ensure sys is imported if using this. For now, just logging.
