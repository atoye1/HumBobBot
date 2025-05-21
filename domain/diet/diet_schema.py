import os
import re

from typing import Any, List
import datetime

from pydantic import BaseModel, Field, validator
from fastapi import UploadFile

from utils.date_util import get_next_monday, get_last_monday
# from constants.cafeteria import * # Commented out as cafeteria_full_name_list is no longer used directly here
import re # Ensure re is imported

class User(BaseModel):
    id: str
    type: str
    properties: dict
    
class UserRequest(BaseModel):
    timezone: str
    utterance: str
    user: User
    
class DietSkill(BaseModel):
    intent: dict
    userRequest: UserRequest
    bot: dict
    action: dict

# (Other existing imports and schema classes like User, UserRequest, DietSkill should remain)

class DietUploadFormSchema(BaseModel):
    post_title: str
    post_create_date_str: str 
    # upload_file: UploadFile # No longer needed here, FastAPI handles it in Form()

    @validator('post_create_date_str')
    def validate_post_create_date_format(cls, value):
        if not re.fullmatch(r'^\d{6}$', value):
            raise ValueError('post_create_date_str must be in yymmdd format')
        return value

"""
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
    utterance: str
    location: str # This will now be a required field provided externally
    # Field(default='') and __init__ are removed.



