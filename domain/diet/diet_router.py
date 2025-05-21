from typing import Union

from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import JSONResponse

from starlette import status # Ensure status is imported
from sqlalchemy.orm import Session
import re # Ensure re is imported

from database import get_db
# from models import Diet # May not be needed if not directly used
# from domain.diet import diet_crud, diet_schema # diet_crud and parts of diet_schema still needed
from domain.diet import diet_crud, diet_schema # Keep diet_schema for DietSkill, DietUtterance
# from domain.diet.diet_service import DietUploadService, ProcessedDietData # ProcessedDietData not used here
from domain.diet.diet_service import DietUploadService, determine_location_from_utterance # Import new function
from response_generator import DietsCarouselResponse


router = APIRouter(
    prefix="/diet",
)

@router.post('/skill')
def diet_skill(_diet_skill: diet_schema.DietSkill, db: Session = Depends(get_db)):
    user_utterance = _diet_skill.userRequest.utterance
    
    determined_location = determine_location_from_utterance(user_utterance)
    
    if not determined_location:
        # Return a message if location is not found or cannot be determined
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

    # Create DietUtterance with the now determined location
    # The DietUtterance schema itself is now simpler.
    # The diet_crud.get_weekly_diets function expects a DietUtterance object
    # which has a .location attribute.
    diet_request_data = diet_schema.DietUtterance(
        utterance=user_utterance,
        location=determined_location
    )
    
    diets = diet_crud.get_weekly_diets(db, diet_request_data) # Pass the new object
    
    if not diets:
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
    response = DietsCarouselResponse(diets)
    return response.to_json()


# multipart-form 이라서 pydantic schema를 바로 사용할 수 없다.
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_diet(post_title: str = Form(),
                      post_create_date_form_field: str = Form(..., alias="post_create_date"), 
                      upload_file: UploadFile = File(), 
                      db:Session = Depends(get_db)): # db might be unused temporarily
    if "image" not in upload_file.content_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not valid image file") # Corrected status code

    # Validate format of post_create_date_form_field
    if not re.fullmatch(r'^\d{6}$', post_create_date_form_field):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="post_create_date must be in yymmdd format") # Corrected status code

    service = DietUploadService()
    try:
        processed_data = service.process_diet_upload_data(
            post_title=post_title,
            post_create_date_str=post_create_date_form_field,
            upload_file_name=upload_file.filename 
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # Corrected status code

    # Call updated CRUD functions
    diet_crud.create_diet(db, data=processed_data) # Pass ProcessedDietData object
    await diet_crud.save_image(upload_file=upload_file, img_path_str=processed_data.img_path) # Pass UploadFile and img_path string

    return JSONResponse(content={
        "message": "Image uploaded successfully and diet information saved.", # Updated message
        "image_url": processed_data.img_url,
        "start_date": processed_data.start_date.strftime("%y%m%d"),
        "post_title": processed_data.post_title,
        "post_create_date": processed_data.post_create_date.strftime("%y%m%d"),
        "cafeteria_id": processed_data.cafeteria_id
    })