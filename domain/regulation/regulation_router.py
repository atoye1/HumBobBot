from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from database import  get_db

from database import SessionLocal
from models import Regulation
from domain.regulation import regulation_crud, regulation_schema

router = APIRouter(
    prefix="/regulation",
)

@router.post('/skill')
def regulation_skill(_regulation_skill: regulation_schema.RegulationSkill,
                     db:Session = Depends(get_db)):
    _regulation_list = db.query(Regulation).order_by(Regulation.create_date.desc()).all()
    return _regulation_list

@router.post('/update')
def regulation_update():
    pass