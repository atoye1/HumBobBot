import os
import shutil
from typing import List
import logging # Add logging

import datetime
from models import Diet
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import UploadFile # NEW import

from domain.cafeteria.cafeteria_crud import get_cafeteria_id
# from domain.diet.diet_schema import * # Remove old schema imports if not needed for DietUtterance
from domain.diet.diet_schema import DietUtterance # Keep only what's needed
from domain.diet.diet_service import ProcessedDietData # NEW import

from utils.date_util import get_next_monday, get_last_monday

logger = logging.getLogger(__name__) # Add logger instance

def get_weekly_diets(db: Session, diet_utterance:DietUtterance) -> List[Diet]:
    cafeteria_id = get_cafeteria_id(db, diet_utterance.location)
    today = datetime.date.today()
    today_datetime = datetime.datetime(today.year, today.month, today.day)
    
    diets_from_db = db.query(Diet).filter( # Renamed to avoid confusion in loop
        or_(
            Diet.start_date == get_last_monday(today_datetime),
            Diet.start_date == get_next_monday(today_datetime)
        )
    ).filter(
        Diet.cafeteria_id == cafeteria_id
    ).all()
    
    # TODO: check file exists를 수행해야한다. -> Implementation below
    
    if not diets_from_db:
        return []

    # Option: Filter list to only include diets with existing images
    # verified_diets = []
    for diet in diets_from_db:
        if diet.img_path: # Check if img_path is not None or empty
            abs_img_path = os.path.join(os.getcwd(), diet.img_path)
            if not os.path.exists(abs_img_path):
                logger.warning(f"Diet image file not found for cafeteria ID {diet.cafeteria_id}, start date {diet.start_date}: {abs_img_path}")
                # If filtering: continue
            # else:
            #    if filtering: verified_diets.append(diet)
        else:
            logger.warning(f"Diet entry for cafeteria ID {diet.cafeteria_id}, start date {diet.start_date} has no img_path.")
            # If filtering: continue

    # For now, as per plan, return all diets from DB after logging.
    # If filtering was chosen, would return 'verified_diets'
    return diets_from_db 

# def create_diet(db: Session, diet_upload: DietUpload) -> None: # OLD signature
def create_diet(db: Session, data: ProcessedDietData) -> None: # NEW signature
    db_diet = db.query(Diet).filter_by(
        cafeteria_id=data.cafeteria_id, # Use data.cafeteria_id
        start_date=data.start_date      # Use data.start_date
    ).first()

    if db_diet: # Update existing
        db_diet.post_title = data.post_title
        db_diet.post_create_date = data.post_create_date # Already datetime
        db_diet.img_url = data.img_url
        db_diet.img_path = data.img_path
    else: # Create new
        db_diet = Diet(
            post_title=data.post_title,
            post_create_date=data.post_create_date, # Already datetime
            start_date=data.start_date,             # Already datetime
            cafeteria_id=data.cafeteria_id,
            img_url=data.img_url,
            img_path=data.img_path
        )
        db.add(db_diet)
    db.commit()

# async def save_image(diet_upload: DietUpload) -> None: # OLD signature
async def save_image(upload_file: UploadFile, img_path_str: str) -> None: # NEW signature
    abs_img_path = os.path.join(os.getcwd(), img_path_str) # Use img_path_str
    if not os.path.exists(os.path.dirname(abs_img_path)):
        os.makedirs(os.path.dirname(abs_img_path))
    
    upload_file_content = await upload_file.read() # Read from passed UploadFile object
    with open(abs_img_path, "wb") as buffer:
        buffer.write(upload_file_content)