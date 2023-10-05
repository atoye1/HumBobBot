from database import SessionLocal
from domain.cafeteria.cafeteria_crud import get_cafeteria_id

db = SessionLocal()
assert get_cafeteria_id(db, '본사') == 1
assert get_cafeteria_id(db, '노포') == 1