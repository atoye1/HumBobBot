import socket
from typing import List
from utils.os_util import check_file_exist
from utils.date_util import get_next_monday

from urllib.parse import urlunparse
import datetime

from models import Diet


def get_diet_img_url(request_url, start_date, location):
    new_path = request_url.path.replace(
        '/get_diet', f'/image/diet/{start_date}_{location}.jpg')
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


def get_schedule_string(location):
    if location == '노포':
        return "조식 : 07:00 - 10:00 | 중식 : 12:00 - 15:00 | 석식 : 17:00 - 20:00"
    elif location == '신평':
        return "조식 : 06:50 - 10:00 | 중식 : 12:00 - 15:00 | 석식 : 16:50 - 20:00"
    elif location == '광안':
        return "조식 : 미운영         | 중식 : 11:30 - 14:30 | 석식 : 16:30 - 19:30"
    elif location == '호포':
        return "조식 : 07:30 - 10:00 | 중식 : 12:00 - 15:00 | 석식 : 17:15 - 20:00"
    else:
        return ''


def generate_carousel_cards(request_url, start_date, location):
    diet_img_url = get_diet_img_url(request_url, start_date, location)
    file_name = diet_img_url.split('/')[-1]

    if not check_file_exist(file_name):
        raise FileNotFoundError(file_name)

    result = []
    result.append(
        {
            "title": f"{location} 주간식단표 ({start_date} 부터)",
            "description": get_schedule_string(location),
            "thumbnail": {
                "imageUrl": diet_img_url,
                "link": {
                    "web": diet_img_url
                }
            },
        }
    )

    next_monday = get_next_monday(
        datetime.datetime.strptime(start_date, "%y%m%d"))
    next_date = next_monday.strftime("%y%m%d")
    next_diet_img_url = get_diet_img_url(request_url, next_date, location)
    next_file_name = next_diet_img_url.split('/')[-1]
    if check_file_exist(next_file_name):
        result.append(
            {
                "title": f"{location} 주간식단표 ({next_date} 부터)",
                "description": get_schedule_string(location),
                "thumbnail": {
                    "imageUrl": next_diet_img_url,
                    "link": {
                        "web": next_diet_img_url
                    }
                },
            }
        )
    return result

class DietsCarouselResponse:
    def __init__(self, diets: List[Diet]):
        self.template = {
           "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": []
                        }
                    }
                ]
            }
        }
        self.diets = diets
        self.host_scheme = 'http'
        self.host_domain = socket.gethostbyname(socket.gethostname())
        self.host_port = 8000
        self.host_netloc = f'{self.host_domain}:{self.host_port}'
        if len(self.diets) == 0:
            raise ValueError("Must contain more than 1 diet results from DB")
    
    def get_absolute_url(self, img_url):
        return urlunparse((
        self.host_scheme,
        self.host_netloc,
        img_url,
        '',
        '',
        '',
    ))

    def to_json(self):
        items = self.template['template']['outputs'][0]['carousel']['items']
        for diet in self.diets:
            items.append({
                "title": f"{diet.cafeteria.location} 주간식단표 ({diet.start_date.date()} 부터)",
                "description": get_schedule_string(diet.cafeteria.location),
                "thumbnail": {
                    "imageUrl": self.get_absolute_url(diet.img_url),
                    "link": {
                        "web": self.get_absolute_url(diet.img_url)
                    }
                },
            }
        )
        return self.template

class DietsErrorResponse:
    def __init__(self):
        pass
    def to_json(self):
        pass
    
    
def generate_response(request_url, start_date, location):
    diet_img_url = get_diet_img_url(request_url, start_date, location)
    file_name = diet_img_url.split('/')[-1]
    print(file_name)
    if check_file_exist(file_name):
        # generate_carousel_cards(request_url, start_date, location)
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "carousel": {
                            "type": "basicCard",
                            "items": generate_carousel_cards(request_url, start_date, location)
                        }
                    }
                ]
            }
        }
    else:
        return {
            "version": "2.0",
            "template": {
                "outputs": [
                        {
                            "basicCard": {
                                "title": f"{location} 주간식단표 ({start_date}) 를 찾지 못했습니다.",
                                "description": '',
                                "thumbnail": {
                                    "imageUrl": get_error_img_url(request_url),
                                },
                            }
                        }
                ]
            }

        }


def generate_rule_cards(request, rules):
    result = []
    base_url = str(request.base_url)
    for rule in rules:
        rule['web_url'] = base_url + 'regulation' + '/' + \
            rule['title'].replace(' ', '_') + '_' + \
            rule['created_at'] + '/' + 'index.xhtml'
        result.append(
            {
                "title": rule['title'],
                "description": rule['created_at'],
                "thumbnail": {
                    "imageUrl": "https://www.public25.com/news/photo/202001/1247_889_429.jpg"
                },
                "buttons": [
                    {
                        "action":  "webLink",
                        "label": "바로보기",
                        "webLinkUrl": rule['web_url']
                    },
                    {
                        "action":  "webLink",
                        "label": "다운로드",
                        "webLinkUrl": rule['file_url']
                    }
                ]
            }
        )

    return result
