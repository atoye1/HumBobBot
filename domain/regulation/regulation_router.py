from fastapi import APIRouter

from database import SessionLocal
from models import Regulation

router = APIRouter(
    prefix="/skill/rule",
)

@router.get('/list')
def question_list():
    db = SessionLocal()
    _question_list = db.query(Question).order_by(Question.create_date.desc()).all()
    db.close()
    return _question_lis