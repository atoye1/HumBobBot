from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from models.Cafeteria import Cafeteria
from database import Base

class Diet(Base):
    __tablename__ = "diet"
    
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

    cafeteria_id = Column(Integer, ForeignKey("cafeteria.id"))
    cafeteria = relationship("Cafeteria", backref="diets")