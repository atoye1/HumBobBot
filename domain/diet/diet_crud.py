import os
import shutil
from typing import List

import datetime
from models import Diet
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from domain.cafeteria.cafeteria_crud import get_cafeteria_id
from domain.diet.diet_schema import DietUpload

def get_weekly_diets(db: Session, utterance:str) -> List[Diet]:
    # 여기서 발화내용을 검증한다.
    now = datetime.datetime.now()
    last_monday = now - datetime.timedelta(days=(now.weekday() + 7 - 0) % 7)  # 0 is Monday's weekday
    next_monday = last_monday + datetime.timedelta(days=7)
    cafeteria_id = get_cafeteria_id(utterance)
    diets= db.query(Diet).filter(
        or_(
            Diet.start_date == last_monday,
            Diet.start_date == next_monday,
        )
    ).filter(
        Diet.restaurent_id == cafeteria_id
    ).all()
    return diets

def create_diet(db: Session, diet_upload: DietUpload) -> None:
    db_diet = Diet(
        post_title = diet_upload.post_title,
        post_create_date = diet_upload.post_create_date,
        start_date = diet_upload.start_date,
        cafeteria_id = diet_upload.cafeteria_id,
        img_url = diet_upload.img_url,
        img_path = diet_upload.img_path
    )
    db.add(db_diet)
    db.commit()

async def save_image(diet_upload: DietUpload) -> None:
    abs_img_path = os.path.join(os.getcwd(), diet_upload.img_path)
    if not os.path.exists(os.path.dirname(abs_img_path)):
        os.makedirs(os.path.dirname(abs_img_path))
    upload_file_content = await diet_upload.upload_file.read()
    with open(abs_img_path, "wb") as buffer:
        buffer.write(upload_file_content)
        # shutil.copyfileobj(upload_file_content, buffer)