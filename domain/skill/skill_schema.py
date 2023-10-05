from typing import List
import datetime

from pydantic import BaseModel, validator, HttpUrl


# 답변 등록 API는 post 방식이고 content라는 입력 항목이 있다.
# 스키마를 사용하지 않고 라우터 함수의 매개변수에만 지정해서 해당 값을 읽을 순 없다.
# get메서드가 아닌 메서드는 Pydantic 스키마로만 읽을 수 있기 때문이다.

class TemplateOutput(BaseModel):
    # TemplateOutput을 carousel, basiccard 등 다양하게 변경하기 위한 추상계층
    pass

class Template(BaseModel):
    outputs: List[TemplateOutput]
    
class KakaoSkillResponse(BaseModel):
    version : str = "2.0"
    template : Template

class CarouselItem(BaseModel):
    type: str
    items: List[dict]

class CarouselOutput(TemplateOutput):
    carousel: CarouselItem

class CarouselResponse(KakaoSkillResponse):
    template: Template = Template(outputs=[CarouselOutput])
    

class Thumbnail(BaseModel):
    imageUrl: HttpUrl

class BasicCard(BaseModel):
    title: str
    description: str
    thumbnail: Thumbnail

class BasicCardOutput(TemplateOutput):
    basicCard: BasicCard

class BasicCardResponse(KakaoSkillResponse):
    template: Template = Template(outputs=[BasicCardOutput])

bc = BasicCardResponse(
    template=Template(
        outputs=[
            BasicCardOutput(
                basicCard= BasicCard(
                    title='not found',
                    description= '',
                    thumbnail=Thumbnail(
                        imageUrl='http://example.com'
                    )
                )
            )
        ]
    )
)

print(bc.__dict__())