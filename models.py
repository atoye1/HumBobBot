from pydantic import BaseModel
from fastapi import UploadFile


class ImageRequest(BaseModel):
    datetime: str
    location: str
    image: UploadFile
