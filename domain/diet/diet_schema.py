# domain/diet/diet_schema.py
"""
This module defines Pydantic schemas used for data validation and serialization
related to diet functionalities. These schemas are primarily used in API endpoints
for request and response validation.

It includes schemas for:
- User information and requests from the chatbot platform.
- Diet skill invocation payloads.
- Forms for uploading diet information.
- Structures for handling user utterances about diets.
"""
import os
import re # re was imported twice, removed one
from typing import Any, List
import datetime

from pydantic import BaseModel, Field, validator
from fastapi import UploadFile # Though UploadFile is commented out in DietUploadFormSchema,
                               # it's good to keep for context or future use if form handling changes.

from utils.date_util import get_next_monday, get_last_monday
# from constants.cafeteria import * # No longer needed due to service layer handling

class User(BaseModel):
    """Represents a user interacting with the chatbot, as per the chatbot platform's structure."""
    id: str
    type: str
    properties: dict # Could be further defined if specific properties are consistently used

class UserRequest(BaseModel):
    """Represents a user's request to the chatbot, containing utterance and user details."""
    timezone: str
    utterance: str
    user: User
    
class DietSkill(BaseModel):
    """
    Represents the payload received when the diet-related skill is invoked by the chatbot.
    
    This typically includes the user's intent, the original user request, bot information,
    and the action to be performed.
    """
    intent: dict # Could be a more specific Pydantic model if intent structure is known
    userRequest: UserRequest
    bot: dict    # Could be a more specific Pydantic model
    action: dict # Could be a more specific Pydantic model


class DietUploadFormSchema(BaseModel):
    """
    Schema for validating the form data when uploading new diet information.
    
    This schema is used to validate the text fields submitted along with the
    diet image file. The file itself (`upload_file`) is handled directly by
    FastAPI's `File()` in the endpoint.
    """
    post_title: str = Field(..., description="The title of the diet post (e.g., '11월 27일 주간식단').")
    post_create_date_str: str = Field(..., description="The creation date of the post as a string in 'yymmdd' format (e.g., '231127').")

    @validator('post_create_date_str')
    def validate_post_create_date_format(cls, value):
        """Validates that post_create_date_str is in 'yymmdd' format."""
        if not re.fullmatch(r'^\d{6}$', value):
            raise ValueError('post_create_date_str must be in yymmdd format')
        return value

"""
# (The old DietUpload class remains commented out for reference)
# This is the start of commenting out the old DietUpload class
class DietUpload(BaseModel):
    post_title: str
    post_create_date: str | datetime.datetime # Note: original had datetime here too
    upload_file: UploadFile
    img_url : str = Field(default = "")
    img_path: str = Field(default = "")
    start_date: str = Field(default = "") # Note: original had this as str too
    cafeteria_id: str= Field(default = "") # Note: original had this as str
    candidates: List[str] = [] # cafeteria_full_name_list # This constant is removed

    def __init__(self, **data:Any):
        super().__init__( **data)
        self.set_additional_attributes()

    def set_additional_attributes(self):
        self.post_create_date = datetime.datetime.strptime(self.post_create_date, '%y%m%d')
        self.set_start_date()
        self.set_cafeteria_id()
        self.set_img_url_path()
    
    def set_cafeteria_id(self):
        # for idx, elem in enumerate(self.candidates):
        #     if elem in self.post_title:
        #         if elem == '안평':
        #             idx -= 1
        #         self.cafeteria_id = idx + 1
        #         return
        raise ValueError('Invalid cafeteria name - Logic moved to service')

    def set_img_url_path(self):
        if not self.cafeteria_id:
            raise ValueError('Invalid cafeteria id - Logic moved to service')
        # img_filename = f'{datetime.datetime.strftime(self.start_date, "%y%m%d")}_{self.candidates[self.cafeteria_id - 1]}.jpg'
        # self.img_url = f'image/diet/{img_filename}'
        # self.img_path = os.path.join('assets', 'image', 'diet', img_filename)
        raise ValueError('Logic moved to service')
    
    def extract_date_from_title(self):
        # ... (omitting full logic for brevity, but it was here)
        # date_patterns = [
        #     r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}\b",
        #     # ... other patterns ...
        # ]
        # ... rest of the method ...
        # return get_last_monday(datetime_list[0]) # Example return
        raise ValueError("Logic moved to service")


    def set_start_date(self):
        # self.start_date = self.extract_date_from_title() or get_next_monday(self.post_create_date) 
        raise ValueError("Logic moved to service")
# This is the end of commenting out the old DietUpload class
"""
    
class DietUtterance(BaseModel):
    """
    Represents a user's utterance related to diet queries.
    
    The `location` field is now expected to be determined by the
    `determine_location_from_utterance` service function and then
    passed to this schema.
    """
    utterance: str = Field(..., description="The raw text input from the user regarding a diet query.")
    location: str = Field(..., description="The canonical cafeteria name determined from the utterance (e.g., '본사').")



