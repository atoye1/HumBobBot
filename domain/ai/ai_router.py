# import os # Removed
# import openai # Removed
from domain.ai import ai_crud
from domain.ai.ai_schema import KakaoChatRequestSchema # Added

from fastapi import APIRouter # Request removed

router = APIRouter(
    prefix="/ai",
    tags=["ai"], # Added tags for API documentation
)

@router.post('/skill', summary="Process AI chat request from Kakao chatbot")
async def ai_skill(kakaorequest: KakaoChatRequestSchema): # NEW signature
    """
    Handles AI-driven chat requests from the Kakao chatbot platform.

    This endpoint receives a payload conforming to `KakaoChatRequestSchema`,
    processes it using the `ai_crud.ai_chat` function, and returns the
    AI-generated response.

    Args:
        kakaorequest (KakaoChatRequestSchema): The validated request payload
                                               from the Kakao skill.

    Returns:
        The response from `ai_crud.ai_chat`, typically a Kakao-compatible
        JSON response object.
    """
    # FastAPI automatically validates and parses the request body into KakaoChatRequestSchema
    return ai_crud.ai_chat(kakaorequest) # Pass the Pydantic model instance

# The /ai/update endpoint is removed as per instructions.
# @router.post('/update')
# def regulation_update():
#     pass
