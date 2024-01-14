import os
import re

from typing import Any, List
import datetime

from pydantic import BaseModel, Field, validator
from fastapi import UploadFile

from utils.date_util import get_next_monday, get_last_monday
from constants.cafeteria import *

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
    
class DietUpload(BaseModel):
    post_title: str
    post_create_date: str | datetime.datetime
    upload_file: UploadFile
    img_url : str = Field(default = "")
    img_path: str = Field(default = "")
    start_date: str = Field(default = "")
    cafeteria_id: str= Field(default = "")
    candidates: List[str] = cafeteria_full_name_list

    def __init__(self, **data:Any):
        super().__init__( **data)
        self.set_additional_attributes()

    def set_additional_attributes(self):
        self.post_create_date = datetime.datetime.strptime(self.post_create_date, '%y%m%d')
        self.set_start_date()
        self.set_cafeteria_id()
        self.set_img_url_path()
    
    def set_cafeteria_id(self):
        for idx, elem in enumerate(self.candidates):
            if elem in self.post_title:
                if elem == '안평':
                    idx -= 1
                # db의 외래키는 1부터 시작하므로 +1 해줘야 한다.
                self.cafeteria_id = idx + 1
                return
        raise ValueError('Invalid cafeteria name')

    def set_img_url_path(self):
        if not self.cafeteria_id:
            raise ValueError('Invalid cafeteria id')
        # TODO cafeteria db와 연동하는 로직 필요. 현재는 하드코딩 되어있음
        img_filename = f'{datetime.datetime.strftime(self.start_date, "%y%m%d")}_{self.candidates[self.cafeteria_id - 1]}.jpg'
        self.img_url = f'image/diet/{img_filename}'
        self.img_path = os.path.join('assets', 'image', 'diet', img_filename)
    
    def extract_date_from_title(self):
        date_patterns = [
            r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}\b",
            r"\b\d{4}/\d{1,2}/\d{1,2}\b",  # YYYY/MM/DD
            r"\b\d{1,2}/\d{1,2}\b",        # MM/DD
            r"\b\d{1,2}\.\d{1,2}\b",        # MM.DD
            r"\b\d{4}-\d{1,2}-\d{1,2}\b",  # YYYY-MM-DD
            r"\b\d{1,2}-\d{1,2}\b",  # MM-DD
            r"\b\d{1,2}월\s?\d{1,2}일\b",
        ]

        date_regex = re.compile("|".join(date_patterns))
        extracted_dates = date_regex.findall(self.post_title)

        extracted_dates = [
            date.replace(".", "/").replace("-", "/").replace("월", "/").replace("일", "").replace(" ", "")
            for date in extracted_dates
        ]

        if not extracted_dates:
            return None

        datetime_list = []
        year = datetime.datetime.now().year
        for date in extracted_dates:
            splitted_date = date.split('/')
            if len(splitted_date) == 3:
                splitted_date = splitted_date[1:]
            month, day = splitted_date
            datetime_list.append(datetime.datetime(year, int(month), int(day)))
        datetime_list.sort()

        return get_last_monday(datetime_list[0])

    def set_start_date(self):
        """
            포스트 제목에서 날짜를 찾을 수 있으면, 해당 날짜가 시작일
            해당 날짜가 월요일이 아니면 월요일로 변경하고 시작일로 저장한다.
            날짜는 정규식으로 패턴을 찾는다.
            포스트가 작성된 날 다음의 첫번째 월요일이 시작일이다.
        """
        self.start_date = self.extract_date_from_title(self) or get_next_monday(self.post_create_date) 

class DietUtterance(BaseModel):
    utterance: str
    location: str = Field(default='')
    
    def __init__(self, **data:Any):
        super().__init__( **data)
        self.set_location()  # Call set_location before the super().__init__
    
    def set_location(self):
        for full_name, semi_name in zip(cafeteria_full_name_list, cafeteria_semi_name_list):
            if full_name in self.utterance or semi_name in self.utterance:
                full_name = '경전철' if full_name == '안평' else full_name
                self.location = full_name
                return
        raise ValueError("Invalid Location")



