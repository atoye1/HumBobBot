# domain/ai/ai_crud.py
"""
Handles AI model interactions, including calls to OpenAI for text and image generation,
and manages responses for a Kakao chatbot interface. Implements an in-memory cache
for handling asynchronous responses and a timeout mechanism.

The OpenAI API key is expected to be set as an environment variable `OPENAI_API_KEY`.
"""
import os
import openai
import threading
import time
import queue as q
from dotenv import load_dotenv
import datetime
import logging # For logging errors and info

import config # Import the config module
from domain.ai.ai_schema import KakaoChatRequestSchema # For type hinting if needed

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
logger = logging.getLogger(__name__)

# In-memory cache for user responses.
# This cache stores pending AI responses that are being generated in a separate thread.
# When a user requests a response that takes longer than the API gateway timeout,
# a placeholder message is sent. The actual response, once generated, is stored here.
# The user can then retrieve it using a "답변 조회" (check response) message.
# Structure: 
# { 
#   user_id (str): {
#     "type": "text" | "image",  # Type of the response
#     "data": "content_or_url",  # The generated text or image URL
#     "prompt": "original_prompt",# The original prompt for context
#     "timestamp": datetime_obj   # When the entry was created, for TTL management
#   } 
# }
user_responses_cache = {}
# CACHE_TTL_SECONDS is now sourced from config.AI_RESPONSE_CACHE_TTL_SECONDS


def text_response_format(bot_response: str) -> dict:
    """
    Formats a text string into the Kakao chatbot's simpleText response structure.
    """
    response = {
        "version":"2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": bot_response
                    }
                }
            ],
            "quickReplies": [ # Empty quickReplies can be omitted if not needed
            ]
        }
    }
    return response

def image_response_format(image_url: str, alt_text_prompt: str) -> dict:
    """
    Formats an image URL into the Kakao chatbot's simpleImage response structure.
    """
    output_text = alt_text_prompt + " 내용에 관한 이미지입니다." # Construct alt text
    response = {
        "version":"2.0",
        "template": {
            "outputs": [
                {
                    "simpleImage": {
                        "imageUrl": image_url,
                        "altText": output_text
                    }
                }
            ],
            "quickReplies": [
            ]
        }
    }
    return response


def timeover() -> dict:
    """
    Generates a Kakao response indicating that AI generation is in progress
    and provides a quick reply button for the user to check back.
    """
    response = {
        "version":"2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": "답변 생성중입니다. \n잠시 후 아래 말풍선을 눌러 생성된 답변을 확인해주세요." # Slightly rephrased
                    }
                }
            ],
            "quickReplies": [
                {
                    "action": "message",
                    "label": "생성된 답변 조회", # Check generated response
                    "messageText": "답변 조회"
                }
            ]
        }
    }
    return response

def get_text_from_gpt(prompt: str) -> str:
    """
    Generates a text response from OpenAI's GPT model using the ChatCompletion API.
    
    The system prompt and model are configured via `config.py`.
    OpenAI API key must be set as an environment variable.

    Args:
        prompt (str): The user's input prompt.

    Returns:
        str: The text content of the AI's response.
    
    Raises:
        openai.APIError: If there's an issue with the OpenAI API call.
    """
    messages_prompt = [
        {"role": "system", "content": config.OPENAI_GPT_SYSTEM_PROMPT},
    ]
    messages_prompt.append({"role": "user", "content": prompt}) # Use append for clarity
    
    # Call OpenAI API
    response = openai.ChatCompletion.create(
        messages=messages_prompt, 
        model=config.OPENAI_GPT_MODEL
    )
    message = response['choices'][0]['message']['content']
    return message


def get_image_url_from_dalle(prompt: str) -> str:
    """
    Generates an image URL from OpenAI's DALL-E model using the Image API.

    The image size is configured via `config.py`.
    OpenAI API key must be set as an environment variable.

    Args:
        prompt (str): The user's input prompt for image generation.

    Returns:
        str: The URL of the generated image.

    Raises:
        openai.APIError: If there's an issue with the OpenAI API call.
    """
    response = openai.Image.create(
        prompt=prompt, 
        n=1, # Number of images to generate
        size=config.OPENAI_DALLE_IMAGE_SIZE
    )
    image_url = response['data'][0]['url']
    return image_url
    
def ai_chat(kakaorequest: KakaoChatRequestSchema) -> dict:
    """
    Main entry point for handling AI chat requests.

    It uses a separate thread to call OpenAI APIs (`response_openai` function)
    to avoid blocking the main FastAPI event loop, especially for potentially
    long-running AI generation tasks.
    A queue is used to get the response back from the thread.
    If the AI response is not generated within a configured timeout 
    (`config.AI_THREAD_TIMEOUT_SECONDS`), a `timeover` message is returned,
    prompting the user to check back later.

    Args:
        kakaorequest (KakaoChatRequestSchema): The validated request payload from Kakao.

    Returns:
        dict: A Kakao-compatible JSON response.
    """
    run_flag = False
    start_time = time.time()
    
    response_queue = q.Queue()
    # The response_openai function is executed in a separate thread
    request_respond_thread = threading.Thread(
        target=response_openai, 
        args=(kakaorequest, response_queue) # Pass the full request and queue
    )
    request_respond_thread.start()
    
    # Wait for the thread to produce a response or timeout
    while (time.time() - start_time < config.AI_THREAD_TIMEOUT_SECONDS): 
        if not response_queue.empty():
            response = response_queue.get()
            run_flag = True
            break
        else:
            time.sleep(0.1) # Brief pause to avoid busy-waiting
    
    if not run_flag: 
        # If timeout occurred, return the timeover message
        response = timeover()
    
    return response

def response_openai(kakaorequest: KakaoChatRequestSchema, response_queue: q.Queue):
    """
    Handles the actual OpenAI API calls and response caching in a separate thread.

    This function processes the user's utterance to determine the action:
    - "답변 조회": Retrieves a cached response for the user.
    - "/img <prompt>": Generates an image using DALL-E and caches the result.
    - "/ask <prompt>": Generates text using GPT and caches the result.
    - Other: Returns a default help message.

    Cache entries are managed with a Time-To-Live (TTL) defined by
    `config.AI_RESPONSE_CACHE_TTL_SECONDS`.

    Args:
        kakaorequest (KakaoChatRequestSchema): The request payload from Kakao.
        response_queue (q.Queue): The queue to put the generated response into.
    """
    user_id = kakaorequest.userRequest.user.id
    utterance = kakaorequest.userRequest.utterance.strip() # Strip whitespace

    # --- Cache Cleanup (TTL) ---
    # Remove expired entries from the cache before processing the current request.
    current_time = datetime.datetime.now()
    # Iterate over a copy of keys for safe deletion during iteration
    for uid_in_cache, entry in list(user_responses_cache.items()): 
        if (current_time - entry['timestamp']).total_seconds() > config.AI_RESPONSE_CACHE_TTL_SECONDS:
            try:
                del user_responses_cache[uid_in_cache]
                logger.info(f"Cache entry for user {uid_in_cache} expired and removed.")
            except KeyError:
                logger.warning(f"Attempted to delete already removed cache entry for user {uid_in_cache}.")

    # --- Utterance Processing ---
    if '답변 조회' == utterance: # Exact match for "답변 조회"
        if user_id in user_responses_cache:
            cached_item = user_responses_cache[user_id]
            original_prompt = cached_item['prompt'] # Get original prompt for context
            # Format and send the cached response
            if cached_item['type'] == 'image':
                response_queue.put(image_response_format(cached_item['data'], original_prompt))
            else: # 'text'
                response_queue.put(text_response_format(cached_item['data']))
            # Clear the cache for this user after successful retrieval
            try:
                del user_responses_cache[user_id] 
            except KeyError:
                 logger.warning(f"Attempted to delete already removed cache entry for user {user_id} after retrieval.")
        else:
            # No cached response found or it expired
            response_queue.put(text_response_format("조회할 답변이 없거나 처리 시간이 만료되었습니다. 다시 요청해주세요."))
    
    elif utterance.startswith('/img '):
        prompt = utterance.replace('/img ', '', 1).strip() # Remove prefix, strip whitespace
        if not prompt: # Handle empty prompt after /img
             response_queue.put(text_response_format("이미지 설명을 입력해주세요. 예: /img 귀여운 고양이"))
             return
        try:
            # Call DALL-E for image generation
            image_url = get_image_url_from_dalle(prompt)
            # Cache the successful response
            user_responses_cache[user_id] = {
                "type": "image", 
                "data": image_url, 
                "prompt": prompt, 
                "timestamp": datetime.datetime.now()
            }
            response_queue.put(image_response_format(image_url, prompt))
        except Exception as e:
            logger.error(f"Error calling DALL-E for user {user_id}, prompt '{prompt}': {e}", exc_info=True)
            response_queue.put(text_response_format("이미지 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."))
    
    elif utterance.startswith('/ask '):
        prompt = utterance.replace('/ask ', '', 1).strip() # Remove prefix, strip whitespace
        if not prompt: # Handle empty prompt after /ask
             response_queue.put(text_response_format("질문 내용을 입력해주세요. 예: /ask 오늘 날씨 어때?"))
             return
        try:
            # Call GPT for text generation
            text_response = get_text_from_gpt(prompt)
            # Cache the successful response
            user_responses_cache[user_id] = {
                "type": "text", 
                "data": text_response, 
                "prompt": prompt, 
                "timestamp": datetime.datetime.now()
            }
            response_queue.put(text_response_format(text_response))
        except Exception as e:
            logger.error(f"Error calling GPT for user {user_id}, prompt '{prompt}': {e}", exc_info=True)
            response_queue.put(text_response_format("답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."))
    else:
        # Default help message if no command is matched
        help_text = (
            "안녕하세요! AI 챗봇입니다.\n"
            "'/ask 내용'으로 질문해주세요.\n"
            "'/img 이미지설명'으로 이미지를 요청할 수 있습니다.\n"
            "이전에 요청한 답변은 '답변 조회'로 확인할 수 있습니다."
        )
        response_queue.put(text_response_format(help_text))
