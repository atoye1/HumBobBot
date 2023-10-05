from typing import Union

from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import JSONResponse

from starlette import status 
from sqlalchemy.orm import Session

from database import get_db
from models import Diet
from domain.diet import diet_crud, diet_schema
from response_generator import DietsCarouselResponse

router = APIRouter(
    prefix="/diet",
)

@router.post('/skill')
def diet_skill(_diet_skill: diet_schema.DietSkill, db: Session = Depends(get_db)):
    # db에서 이번주와 다음주의 식단표를 조회한다.
    print(_diet_skill)
    diet_utterance = diet_schema.DietUtterance(utterance = _diet_skill.userRequest.utterance)
    diets = diet_crud.get_weekly_diets(db, diet_utterance)
    if not diets:
        raise HTTPException(status_code=404, detail="Recent diet not found")
    response = DietsCarouselResponse(diets)
    return response.to_json()


# multipart-form 이라서 pydantic schema를 바로 사용할 수 없다.
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_diet(post_title: str = Form(),
                      post_create_date: str = Form(max_length=6, min_length=6), upload_file: UploadFile = File(), db:Session = Depends(get_db)):
    if "image" not in upload_file.content_type:
        raise HTTPException(status_code=400, detail="Not valid image file")

    diet_upload = diet_schema.DietUpload(post_title=post_title,
                                         post_create_date=post_create_date,
                                         upload_file=upload_file)
    diet_crud.create_diet(db, diet_upload)
    await diet_crud.save_image(diet_upload)

    return JSONResponse(content={
        "message": "Image uploaded successfully",
        "image_url": diet_upload.img_url,
        "start_date": diet_upload.start_date.strftime("%y%m%d"),
        "post_title": diet_upload.post_title,
        "post_create_date": diet_upload.post_create_date.strftime("%y%m%d"),
    })