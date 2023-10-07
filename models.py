from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, func, Enum
from sqlalchemy.orm import relationship
from database import Base

class Diet(Base):
    __tablename__ = "diets"
    
    id = Column(Integer, primary_key=True)
    img_url = Column(String(length=500), nullable=False)
    img_path = Column(String(length=500), nullable=False)

    post_title = Column(String(length=200), nullable=False)
    post_create_date = Column(DateTime, nullable=False)

    create_date = Column(DateTime, nullable=False,
                         default=func.now())
    update_date = Column(DateTime, nullable=False,
                         default=func.now(),
                         onupdate=func.now())
    start_date = Column(DateTime, nullable=False)

    cafeteria_id = Column(Integer, ForeignKey("cafeterias.id"))
    cafeteria = relationship("Cafeteria", backref="diets")

class Cafeteria(Base):
    __tablename__ = "cafeterias"
    
    id = Column(Integer, primary_key=True)

    address = Column(String(length=200), nullable=False)
    location = Column(String(length=50), nullable=False)
    phone = Column(String(length=50), nullable=True)

    create_date = Column(DateTime, nullable=False,
                         default=func.now())
    update_date = Column(DateTime, nullable=False,
                         default=func.now(),
                         onupdate=func.now())

    breakfast_start_time = Column(Time, nullable=True)
    breakfast_end_time = Column(Time, nullable=True)
    lunch_start_time = Column(Time, nullable=True)
    lunch_end_time = Column(Time, nullable=True)
    dinner_start_time = Column(Time, nullable=True)
    dinner_end_time = Column(Time, nullable=True)
    
class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(Integer, primary_key=True)
    title = Column(String(length=100), nullable=False, unique=True)
    type = Column(Enum('법', '시행령', '시행규칙', '정관', '조례', '예규', '규정', '내규'), nullable=True)
    create_date = Column(DateTime, nullable=False)
    update_date = Column(DateTime, nullable=False)
    enforce_date = Column(DateTime, nullable=True)
    file_url = Column(String(length=200), nullable=True)
    html_url = Column(String(length=200), nullable=True)