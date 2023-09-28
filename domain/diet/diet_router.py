from fastapi import APIRouter, Depends
from starlette import status
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Diet

router = APIRouter(
    prefix="/diet",
)

@router.post('/')
def diet():
    db = SessionLocal()
    _diet = db.query(Diet)
    return _diet

@router.post('/upload', response_model=status.HTTP_201_CREATED)
def diet_upload():
    # upload image as file
    # update db
    # return success response
    pass

@router.get('/list')
def question_list():
    db = SessionLocal()
    _question_list = db.query(Question).order_by(Question.create_date.desc()).all()
    db.close()
    return _question_lis

