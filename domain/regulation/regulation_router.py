from fastapi import APIRouter
from sqlalchemy.orm import Session
from starlette import status

from database import  get_db

from database import SessionLocal
from models import Regulation

router = APIRouter(
    prefix="/regulation",
)

@router.post('/skill')
def question_list():
    db = SessionLocal()
    _question_list = db.query(Question).order_by(Question.create_date.desc()).all()
    db.close()
    return _question_lis