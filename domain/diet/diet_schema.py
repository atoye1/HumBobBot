import os

from typing import Any, List
import datetime

from pydantic import BaseModel, Field
from fastapi import UploadFile

from domain.cafeteria.cafeteria_schema import CafeteriaLocationEnum
from utils.date_util import get_next_monday, get_previous_monday

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
    candidates: List[str] = ['본사', '노포', '신평', '호포', '광안', '대저', '경전철', '안평']

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
                self.cafeteria_id = idx
                return
        raise ValueError('Invalid cafeteria name')

    def set_img_url_path(self):
        if not self.cafeteria_id:
            raise ValueError('Invalid cafeteria id')
        img_filename = f'{datetime.datetime.strftime(self.start_date, "%y%m%d")}_{self.candidates[self.cafeteria_id]}.jpg'
        self.img_url = f'image/{img_filename}'
        self.img_path = os.path.join('assets', 'image', 'diet', img_filename)

    def set_start_date(self):
        """
            포스트 제목에서 날짜를 찾을 수 있으면, 해당 날짜가 시작일
            해당 날짜가 월요일이 아니면 월요일로 변경하고 시작일로 저장한다.
            날짜는 정규식으로 패턴을 찾는다.
            포스트가 작성된 날 다음의 첫번째 월요일이 시작일이다.
        """
        # TODO 다른 로직도 추가하기
        self.start_date = get_next_monday(self.post_create_date) 