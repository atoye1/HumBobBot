# domain/diet/diet_router.py
"""
This module defines API routes related to diet information.

It includes endpoints for:
- Retrieving weekly diet information based on user utterances (chatbot skill).
- Uploading new diet information (image and associated metadata).
"""
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import JSONResponse

from starlette import status 
from sqlalchemy.orm import Session
import re 

from database import get_db
from domain.diet import diet_crud, diet_schema 
from domain.diet.diet_service import DietUploadService, determine_location_from_utterance
from response_generator import DietsCarouselResponse


router = APIRouter(
    prefix="/diet",
    tags=["diet"], # Add tags for API documentation
)

@router.post('/skill', summary="Get weekly diet information for a cafeteria")
def diet_skill(_diet_skill: diet_schema.DietSkill, db: Session = Depends(get_db)):
    """
    Handles requests from the chatbot skill to retrieve weekly diet information.

    Based on the user's utterance, it determines the target cafeteria,
    fetches the current and next week's diet data from the database,
    and returns it in a carousel format suitable for the chatbot.

    Args:
        _diet_skill (diet_schema.DietSkill): The payload from the chatbot skill invocation.
        db (Session, optional): Database session dependency. Defaults to Depends(get_db).

    Returns:
        dict: A JSON response formatted for the chatbot, either with diet information
              or a message indicating data unavailability or inability to determine location.
    """
    user_utterance = _diet_skill.userRequest.utterance
    
    # Determine the cafeteria location from the user's utterance
    determined_location = determine_location_from_utterance(user_utterance)
    
    if not determined_location:
        # If location cannot be determined, ask the user to specify
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": "어느 식당의 식단표를 찾으시는지 말씀해주세요 (예: 본사 식단 알려줘)."
                        }
                    }
                ]
            }
        }

    # Prepare data for fetching weekly diets
    diet_request_data = diet_schema.DietUtterance(
        utterance=user_utterance,
        location=determined_location
    )
    
    # Fetch diets from the database
    diets = diet_crud.get_weekly_diets(db, diet_request_data) 
    
    if not diets:
        # If no diet data is found for the location
        return {
                "version": "2.0",
                "template": {
                    "outputs": [
                        {
                            "simpleText": {
                                "text": f"{determined_location} 식당의 식단 데이터가 현재 없습니다. 나중에 다시 확인해주세요."
                            }
                        }
                    ]
                }
            }
            
    # Format the response using DietsCarouselResponse
    response = DietsCarouselResponse(diets)
    return response.to_json()


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload new diet information")
async def upload_diet(
    post_title: str = Form(..., description="Title of the diet post (e.g., '11월 3주차 주간식단표')."),
    post_create_date_form_field: str = Form(..., alias="post_create_date", description="Creation date of the post in 'yymmdd' format (e.g., '231120')."), 
    upload_file: UploadFile = File(..., description="The diet image file (e.g., JPG, PNG)."), 
    db:Session = Depends(get_db)
):
    """
    Uploads a new diet menu, including an image and associated metadata.

    The endpoint processes the uploaded data using `DietUploadService`,
    saves the diet information to the database, and stores the image file.

    Args:
        post_title (str): The title from the form data.
        post_create_date_form_field (str): The post creation date string from the form data.
                                           Aliased as "post_create_date".
        upload_file (UploadFile): The uploaded image file.
        db (Session, optional): Database session dependency. Defaults to Depends(get_db).

    Raises:
        HTTPException: 
            - 400 (Bad Request): If the uploaded file is not a valid image type.
            - 400 (Bad Request): If `post_create_date` is not in 'yymmdd' format.
            - 400 (Bad Request): If the `DietUploadService` raises a ValueError during processing
                                 (e.g., invalid cafeteria name in title).

    Returns:
        JSONResponse: A success message along with details of the uploaded diet,
                      including image URL, start date, title, post creation date,
                      and cafeteria ID.
    """
    # Validate image file type
    if "image" not in upload_file.content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not valid image file")

    # Validate format of post_create_date_form_field (already handled by Pydantic in DietUploadFormSchema if used,
    # but good for direct Form validation if schema isn't used for Form directly)
    if not re.fullmatch(r'^\d{6}$', post_create_date_form_field):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="post_create_date must be in yymmdd format")

    service = DietUploadService()
    try:
        # Process uploaded data using the service
        processed_data = service.process_diet_upload_data(
            post_title=post_title,
            post_create_date_str=post_create_date_form_field,
            upload_file_name=upload_file.filename 
        )
    except ValueError as e: # Catch errors from the service (e.g., invalid cafeteria name)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Perform database operations and file saving
    diet_crud.create_diet(db, data=processed_data) 
    await diet_crud.save_image(upload_file=upload_file, img_path_str=processed_data.img_path)

    # Return success response
    return JSONResponse(content={
        "message": "Image uploaded successfully and diet information saved.",
        "image_url": processed_data.img_url,
        "start_date": processed_data.start_date.strftime("%y%m%d"),
        "post_title": processed_data.post_title,
        "post_create_date": processed_data.post_create_date.strftime("%y%m%d"),
        "cafeteria_id": processed_data.cafeteria_id
    })