
import uvicorn
import json
import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from starlette.requests import Request
from starlette import status

from response_generator import generate_response, generate_rule_cards

from domain.diet import diet_router
from domain.regulation import regulation_router
from domain.ai import ai_router

app = FastAPI(title="Humetro Bob Bot API", version="1.0.0")
startup_time = datetime.datetime.now()

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount('/image', StaticFiles(directory='assets/image'), name='image')
app.mount("/regulation", StaticFiles(directory="assets/html/regulation"), name="regulation")

rules = None
with open('./rules.json', 'r', encoding='utf-8') as f:
    rules = json.load(f)

app.include_router(diet_router.router)
app.include_router(regulation_router.router)
app.include_router(ai_router.router)

@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    current_time = datetime.datetime.now()
    uptime = current_time - startup_time
    return {"msg": "server is up", "uptime":str(uptime)}


@app.post('/get_rules')
async def get_rules(request: Request):
    if rules is None:
        raise HTTPException(status_code=404, detail="No rules are loaded")

    body = await request.body()
    request_body = json.loads(body.decode())
    user_msg_raw = request_body['userRequest']['utterance']
    # filter not worked due to namespace issue -> Fixed!!
    user_msg = user_msg_raw

    for word in ['규정', '내규', '지침', '예규']:
        user_msg = user_msg.replace(word, '')
    user_msg_words = user_msg.split()

    results = []
    for user_msg_word in user_msg_words:
        if not user_msg_word:
            continue
        for rule in rules:
            if user_msg_word in rule['title']:
                results.append(rule)
    if results:
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                       "carousel": {
                           "type": "basicCard",
                           "items": generate_rule_cards(request, results[:10])
                       }
                    }
                ]
            }
        }
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                    {
                        "basicCard": {
                            "title": "관련 규정을 찾지 못했습니다.",
                            "description": f"입력한 메세지 : {user_msg_raw}",
                            "thumbnail": {
                                "imageUrl": "https://user-images.githubusercontent.com/24848110/33519396-7e56363c-d79d-11e7-969b-09782f5ccbab.png",
                            },
                        }
                    }
            ]
        }

    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
