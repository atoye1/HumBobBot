# domain/diet/diet_crud.py
"""
This module provides CRUD (Create, Read, Update, Delete) operations
for Diet (식단) related data in the database.

It includes functions for:
- Fetching weekly diet information for a specified cafeteria.
- Creating or updating diet records based on processed upload data.
- Saving uploaded diet images to the filesystem.
"""
import os
import shutil
from typing import List
import logging 

import datetime
from models import Diet
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import UploadFile 

from domain.cafeteria.cafeteria_crud import get_cafeteria_id
from domain.diet.diet_schema import DietUtterance 
from domain.diet.diet_service import ProcessedDietData 

from utils.date_util import get_next_monday, get_last_monday

logger = logging.getLogger(__name__) 

def get_weekly_diets(db: Session, diet_utterance: DietUtterance) -> List[Diet]:
    """
    Retrieves weekly diet information for a given cafeteria.

    It fetches diet records for the current week (starting from the last Monday)
    and the next week (starting from the next Monday) for the specified cafeteria location.
    It also checks for the existence of the associated image files and logs a warning
    if an image is missing, but does not filter the results based on image presence.

    Args:
        db (Session): The database session.
        diet_utterance (DietUtterance): An object containing the user's utterance
                                        and the determined cafeteria location.

    Returns:
        List[Diet]: A list of Diet model instances for the specified weeks and location.
                    Returns an empty list if no cafeteria ID is found or no diets are available.
    """
    cafeteria_id = get_cafeteria_id(db, diet_utterance.location)
    if not cafeteria_id:
        logger.warning(f"Could not find cafeteria ID for location: {diet_utterance.location}")
        return [] # Return empty list if cafeteria_id is not found

    today = datetime.date.today()
    today_datetime = datetime.datetime(today.year, today.month, today.day)
    
    # Fetch diets for the current week (from last Monday) and next week (from next Monday)
    diets_from_db = db.query(Diet).filter(
        or_(
            Diet.start_date == get_last_monday(today_datetime),
            Diet.start_date == get_next_monday(today_datetime)
        )
    ).filter(
        Diet.cafeteria_id == cafeteria_id
    ).order_by(Diet.start_date).all() # Added order_by for consistent results
    
    if not diets_from_db:
        logger.info(f"No diets found in DB for cafeteria ID {cafeteria_id} for current/next week.")
        return []

    # File existence check for associated images
    for diet in diets_from_db:
        if diet.img_path: 
            # Construct absolute path. Assuming diet.img_path is relative to project root (e.g., 'assets/image/diet/...')
            abs_img_path = os.path.join(os.getcwd(), diet.img_path)
            if not os.path.exists(abs_img_path):
                logger.warning(f"Diet image file not found for cafeteria ID {diet.cafeteria_id}, start date {diet.start_date}: {abs_img_path}")
        else:
            logger.warning(f"Diet entry for cafeteria ID {diet.cafeteria_id}, start date {diet.start_date} has no img_path specified.")

    # Returns all diet entries found in the DB for the period, regardless of image file existence (only logs warnings).
    return diets_from_db 

def create_diet(db: Session, data: ProcessedDietData) -> None:
    """
    Creates a new diet record or updates an existing one in the database.

    This function implements an "upsert" logic:
    - If a Diet record with the same `cafeteria_id` and `start_date` already exists,
      it updates the existing record's fields with the new data.
    - If no such record exists, it creates a new Diet record.

    Args:
        db (Session): The database session.
        data (ProcessedDietData): An object containing the processed diet information
                                  (e.g., from `DietUploadService`).
    """
    # Try to find an existing diet record
    db_diet = db.query(Diet).filter_by(
        cafeteria_id=data.cafeteria_id, 
        start_date=data.start_date      
    ).first()

    if db_diet: 
        # Update existing record
        logger.info(f"Updating existing diet for cafeteria ID {data.cafeteria_id} and start date {data.start_date}.")
        db_diet.post_title = data.post_title
        db_diet.post_create_date = data.post_create_date 
        db_diet.img_url = data.img_url
        db_diet.img_path = data.img_path
    else: 
        # Create a new record
        logger.info(f"Creating new diet for cafeteria ID {data.cafeteria_id} and start date {data.start_date}.")
        db_diet = Diet(
            post_title=data.post_title,
            post_create_date=data.post_create_date, 
            start_date=data.start_date,             
            cafeteria_id=data.cafeteria_id,
            img_url=data.img_url,
            img_path=data.img_path
        )
        db.add(db_diet)
    db.commit() # Commit the session to save changes (either update or new creation)

async def save_image(upload_file: UploadFile, img_path_str: str) -> None:
    """
    Saves an uploaded image file to the specified path.

    It constructs an absolute path from the given `img_path_str` (which is assumed
    to be relative to the project's root directory). If the target directory
    doesn't exist, it creates it. Then, it writes the content of the
    `upload_file` to the target path.

    Args:
        upload_file (UploadFile): The FastAPI `UploadFile` object representing the image.
        img_path_str (str): The relative path (from project root) where the image
                            should be saved (e.g., 'assets/image/diet/filename.jpg').
    """
    # Construct absolute path. img_path_str is expected to be like 'assets/image/diet/...'
    abs_img_path = os.path.join(os.getcwd(), img_path_str) 
    
    # Ensure the target directory exists
    target_dir = os.path.dirname(abs_img_path)
    if not os.path.exists(target_dir):
        logger.info(f"Creating directory for image: {target_dir}")
        os.makedirs(target_dir)
    
    # Read the file content and write it to the destination
    try:
        upload_file_content = await upload_file.read() 
        with open(abs_img_path, "wb") as buffer:
            buffer.write(upload_file_content)
        logger.info(f"Successfully saved image to: {abs_img_path}")
    except Exception as e:
        logger.error(f"Failed to save image to {abs_img_path}: {e}", exc_info=True)
        # Depending on requirements, might want to re-raise or handle differently