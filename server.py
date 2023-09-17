from dataclasses import dataclass
from typing import Dict, Union

import uvicorn
import json
import datetime
import shutil
import os

from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from starlette.requests import Request

from utils import check_file_exist
from response_generator import generate_response

app = FastAPI(title="Humetro Bob Bot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount('/images', StaticFiles(directory='images'), name='images')


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/test_text")
def read_item():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "msg": "교정 결과\n" + "**this is sample text**"
                    }
                }
            ]
        },
        "data": {
            "msg": "msg from HuBobBot!!"
        }
    }


@app.post("/test_image")
def read_image():
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleImage": {
                        "imageUrl": "https://t1.kakaocdn.net/openbuilder/sample/lj3JUcmrzC53YIjNDkqbWK.jpg",
                        "altText": "보물상자입니다"
                    }
                }
            ]
        },
        "data": {
            "msg": "msg from HuBobBot!!"
        }
    }


@app.post("/get_diet")
async def read_card(request: Request):
    def get_location(user_msg):
        full_name_list = ['본사', '노포', '신평', '호포', '광안', '대저', '경전철', '안평']
        semi_name_list = ['ㅂㅅ', 'ㄴㅍ', 'ㅅㅍ', 'ㅎㅍ', 'ㄱㅇ', 'ㄷㅈ', 'ㄱㅈㅊ', 'ㅇㅍ']
        result = None
        for full_name, semi_name in zip(full_name_list, semi_name_list):
            if full_name in user_msg or semi_name in user_msg:
                result = full_name
                break
        result = '경전철' if result == '안평' else result
        return result

    def get_diet_img_url(request_url, start_date, location):
        new_path = request_url.path.replace(
            '/get_diet', f'/images/{start_date}_{location}.jpg')
        result = urlunparse((
            request_url.scheme,
            request_url.netloc,
            new_path,
            '',
            '',
            '',
        ))
        return str(result)

    def get_error_img_url(request_url):
        new_path = request_url.path.replace(
            '/get_diet', f'/images/error.jpg')
        result = urlunparse((
            request_url.scheme,
            request_url.netloc,
            new_path,
            '',
            '',
            '',
        ))
        return str(result)

    def get_last_monday(dt: datetime.datetime) -> str:
        difference = dt.weekday()
        last_monday_date = dt.date() - datetime.timedelta(days=difference)
        return last_monday_date.strftime('%y%m%d')

    def get_next_monday(dt: datetime.datetime) -> str:
        # Find out how many days until next Monday
        difference = (7 - dt.weekday()) % 7
        if difference == 0:  # Today is already Monday, so go to the next one
            difference = 7
        next_monday_date = dt.date() + datetime.timedelta(days=difference)
        return next_monday_date.strftime('%y%m%d')

    body = await request.body()
    request_body = json.loads(body.decode())
    request_url = request.url
    user_msg = request_body['userRequest']['utterance']
    start_date = get_last_monday(datetime.datetime.now())
    location = get_location(user_msg)

    return generate_response(request_url, start_date, location)


@app.post("/upload_diet")
async def save_diet_image(yymmdd: str = Form(), location: str = Form(), file: UploadFile = File()):
    image_directory = "images"  # You can change this to your desired directory
    if not os.path.exists(image_directory):
        os.makedirs(image_directory)
    # Construct the filename
    filename = f"{yymmdd}_{location}.jpg"
    file_path = os.path.join(image_directory, filename)

    # # Save the uploaded image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": filename}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
