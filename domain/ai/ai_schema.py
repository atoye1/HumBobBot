# domain/ai/ai_schema.py
"""
This module defines Pydantic schemas for validating the structure of incoming
requests from the Kakao chatbot platform, specifically for AI-related skills.

These schemas ensure that the request payloads conform to the expected format,
focusing on the parts of the payload that are actively used by the application,
such as the user's utterance and their unique ID.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List # Ensure List is imported here at the top

# class RegulationSkill(BaseModel): # Removed as per instructions
#     pass

class KakaoUserProperties(BaseModel):
    """
    Represents the 'properties' field within the Kakao user object.
    
    This can include various platform-specific user properties.
    It's defined minimally here as its specific sub-fields are not
    directly used in the current AI logic beyond being part of the structure.
    Allows extra fields to accommodate any properties sent by Kakao.
    """
    plusfriendUserKey: Optional[str] = None
    appUserId: Optional[str] = None
    # If other known properties exist and are relevant, they can be added here.

    class Config:
        extra = "allow" # Allow any other properties Kakao might send

class KakaoUserSchema(BaseModel):
    """
    Represents the 'user' object within a Kakao chatbot request.
    
    It contains the user's ID, type, and additional properties.
    The 'id' field is particularly important for user-specific logic or caching.
    """
    id: str = Field(..., description="Unique identifier for the user.")
    type: str = Field(..., description="Type of the user (e.g., '챗봇사용자').")
    properties: Optional[KakaoUserProperties] = Field(None, description="Additional properties of the user provided by Kakao.")

class KakaoUserRequestSchema(BaseModel):
    """
    Represents the 'userRequest' object within a Kakao chatbot request.
    
    This object encapsulates the user's direct interaction, including their
    utterance and details about the user.
    """
    timezone: Optional[str] = Field(None, description="Timezone of the user (e.g., 'Asia/Seoul').")
    utterance: str = Field(..., description="The text of the user's message to the chatbot.")
    user: KakaoUserSchema = Field(..., description="Object containing details about the user.")
    
    # block and params are often included by Kakao, making them optional here.
    block: Optional[Dict[str, Any]] = Field(None, description="Details of the Kakao Block that triggered the request.")
    params: Optional[Dict[str, Any]] = Field(None, description="Parameters extracted from the user's utterance or block.")


class KakaoChatRequestSchema(BaseModel):
    """
    Represents the overall structure of a request payload from the Kakao chatbot skill.

    This is the top-level model for validating incoming chat requests.
    It focuses on the 'userRequest' which contains the essential utterance and user ID.
    Other common fields like 'intent', 'bot', and 'action' are made optional
    as they are not strictly required by the current AI logic using this schema.
    """
    userRequest: KakaoUserRequestSchema = Field(..., description="Contains the user's utterance and user details.")
    
    # Common optional fields in Kakao skill requests:
    intent: Optional[Dict[str, Any]] = Field(None, description="Details about the intent recognized by Kakao.")
    bot: Optional[Dict[str, Any]] = Field(None, description="Information about the bot handling the request.")
    action: Optional[Dict[str, Any]] = Field(None, description="Details about the action being performed.")
    contexts: Optional[List[Dict[str, Any]]] = Field(None, description="Contextual information from previous interactions.")

    # Minimal definition was:
    # userRequest: KakaoUserRequestSchema
    # This expanded version is more representative of a typical Kakao payload
    # while keeping non-essential parts optional for current use.
