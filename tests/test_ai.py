# tests/test_ai.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import time
import datetime
import threading # Added for timeout test

from server import app # Your FastAPI app instance
from domain.ai import ai_crud # To inspect cache or mock functions within if needed
from domain.ai.ai_schema import KakaoChatRequestSchema, KakaoUserRequestSchema, KakaoUserSchema # For constructing requests
import config # To access AI_THREAD_TIMEOUT_SECONDS

client = TestClient(app) # Revert to positional argument

# Sample User ID for tests
TEST_USER_ID = "test_user_123"

def create_kakao_request(utterance: str, user_id: str = TEST_USER_ID) -> KakaoChatRequestSchema:
    return KakaoChatRequestSchema(
        userRequest=KakaoUserRequestSchema(
            timezone="Asia/Seoul",
            utterance=utterance,
            user=KakaoUserSchema(id=user_id, type="talk_user", properties={}) # Ensure properties is a dict
        )
        # Other fields like intent, bot, action are optional and not needed for these tests
    )

# Test for /ask command
@patch('domain.ai.ai_crud.openai.ChatCompletion.create')
def test_ai_skill_ask_command(mock_chat_completion_create):
    # Setup mock for GPT response
    mock_response_content = "This is a mock GPT response."
    mock_chat_completion_create.return_value = {
        'choices': [{'message': {'content': mock_response_content}}]
    }
    
    request_data = create_kakao_request(utterance="/ask What is AI?")
    response = client.post("/ai/skill", json=request_data.dict())
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['template']['outputs'][0]['simpleText']['text'] == mock_response_content
    mock_chat_completion_create.assert_called_once()

    # Check cache
    assert TEST_USER_ID in ai_crud.user_responses_cache
    cached_item = ai_crud.user_responses_cache[TEST_USER_ID]
    assert cached_item['type'] == 'text'
    assert cached_item['data'] == mock_response_content
    assert cached_item['prompt'] == "What is AI?"
    
    # Cleanup cache for next test
    ai_crud.user_responses_cache.pop(TEST_USER_ID, None)

# Test for /img command
@patch('domain.ai.ai_crud.openai.Image.create')
def test_ai_skill_img_command(mock_image_create):
    # Setup mock for DALL-E response
    mock_image_url = "http://example.com/mock_image.png"
    mock_image_create.return_value = {'data': [{'url': mock_image_url}]}
    
    request_data = create_kakao_request(utterance="/img A picture of a cat")
    response = client.post("/ai/skill", json=request_data.dict())
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['template']['outputs'][0]['simpleImage']['imageUrl'] == mock_image_url
    mock_image_create.assert_called_once()

    # Check cache
    assert TEST_USER_ID in ai_crud.user_responses_cache
    cached_item = ai_crud.user_responses_cache[TEST_USER_ID]
    assert cached_item['type'] == 'image'
    assert cached_item['data'] == mock_image_url
    assert cached_item['prompt'] == "A picture of a cat"
    ai_crud.user_responses_cache.pop(TEST_USER_ID, None)

# Test for "답변 조회" (Answer Lookup)
@patch('domain.ai.ai_crud.openai.ChatCompletion.create') # Mocking to ensure it's not called
def test_ai_skill_answer_lookup(mock_chat_completion_create):
    # Populate cache first
    mock_response_content = "Cached GPT answer."
    ai_crud.user_responses_cache[TEST_USER_ID] = {
        "type": "text", 
        "data": mock_response_content, 
        "prompt": "Initial question",
        "timestamp": datetime.datetime.now()
    }
    
    request_data = create_kakao_request(utterance="답변 조회")
    response = client.post("/ai/skill", json=request_data.dict())
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['template']['outputs'][0]['simpleText']['text'] == mock_response_content
    
    # Assert cache is cleared after retrieval
    assert TEST_USER_ID not in ai_crud.user_responses_cache
    mock_chat_completion_create.assert_not_called() # OpenAI should not be called

# Test "답변 조회" when cache is empty
def test_ai_skill_answer_lookup_empty_cache():
    ai_crud.user_responses_cache.pop(TEST_USER_ID, None) # Ensure cache is empty
    request_data = create_kakao_request(utterance="답변 조회")
    response = client.post("/ai/skill", json=request_data.dict())
    
    assert response.status_code == 200
    json_response = response.json()
    assert "조회할 답변이 없거나 처리 시간이 만료되었습니다." in json_response['template']['outputs'][0]['simpleText']['text']

# Test Timeout and then "답변 조회"
@patch('domain.ai.ai_crud.openai.ChatCompletion.create')
def test_ai_skill_timeout_then_lookup(mock_chat_completion_create):
    # Setup mock to simulate delay and then provide a response
    mock_response_content = "Delayed GPT answer."
    api_call_event = threading.Event() # Renamed to avoid conflict

    def delayed_api_call(*args, **kwargs):
        time.sleep(config.AI_THREAD_TIMEOUT_SECONDS + 1) # Sleep longer than timeout
        api_call_event.set() # Signal that the API call 'completed'
        return {'choices': [{'message': {'content': mock_response_content}}]}

    mock_chat_completion_create.side_effect = delayed_api_call
    
    # Initial request that should timeout
    request_data_ask = create_kakao_request(utterance="/ask very_long_question")
    response_timeout = client.post("/ai/skill", json=request_data_ask.dict())
    
    assert response_timeout.status_code == 200
    json_response_timeout = response_timeout.json()
    assert "답변 생성중입니다." in json_response_timeout['template']['outputs'][0]['simpleText']['text']
    
    # Wait for the thread to actually finish and populate cache
    assert api_call_event.wait(timeout=config.AI_THREAD_TIMEOUT_SECONDS + 2), "Thread did not complete in time"
    
    # Now try to lookup the answer
    request_data_lookup = create_kakao_request(utterance="답변 조회")
    response_lookup = client.post("/ai/skill", json=request_data_lookup.dict())
    
    assert response_lookup.status_code == 200
    json_response_lookup = response_lookup.json()
    assert json_response_lookup['template']['outputs'][0]['simpleText']['text'] == mock_response_content
    
    # Cache should be cleared after lookup
    assert TEST_USER_ID not in ai_crud.user_responses_cache
    ai_crud.user_responses_cache.pop(TEST_USER_ID, None) # Cleanup just in case

# Test default response for unmatched utterance
def test_ai_skill_default_response():
    request_data = create_kakao_request(utterance="some random text")
    response = client.post("/ai/skill", json=request_data.dict())
    assert response.status_code == 200
    json_response = response.json()
    # Check for the helpful default message
    expected_default_text = (
        "안녕하세요! AI 챗봇입니다.\n"
        "'/ask 내용'으로 질문해주세요.\n"
        "'/img 이미지설명'으로 이미지를 요청할 수 있습니다.\n"
        "이전에 요청한 답변은 '답변 조회'로 확인할 수 있습니다."
    )
    assert json_response['template']['outputs'][0]['simpleText']['text'] == expected_default_text

# Fixture to clean up cache before and after each test function
@pytest.fixture(autouse=True)
def cleanup_cache():
    ai_crud.user_responses_cache.pop(TEST_USER_ID, None) # Before test
    yield # This is where the test runs
    ai_crud.user_responses_cache.pop(TEST_USER_ID, None) # After test
