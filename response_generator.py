from utils import check_file_exist
from urllib.parse import urlunparse
import datetime
from utils import get_next_monday


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


def get_schedule_string(location):
    if location == '노포':
        return "조식 : 07:00 - 10:00 | 중식 : 12:00 - 15:00 | 석식 : 17:00 - 20:00"
    elif location == '신평':
        return "조식 : 06:50 - 10:00 | 중식 : 12:00 - 15:00 | 석식 : 16:50 - 20:00"
    elif location == '광안':
        return "조식 : 미운영\n중식 : 11:30 - 14:30\n석식 : 16:30 - 19:30"
    elif location == '호포':
        return "조식 : 07:30 - 10:00\n중식 : 12:00 - 15:00\n석식 : 17:15 - 20:00"
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
                        "web": diet_img_url
                    }
                },
            }
        )
    return result


def generate_response(request_url, start_date, location):
    diet_img_url = get_diet_img_url(request_url, start_date, location)
    file_name = diet_img_url.split('/')[-1]
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


def generate_rule_cards(rules):
    result = []
    for rule in rules:
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
                        "label": "다운로드",
                        "webLinkUrl": rule['file_url']
                    }
                ]
            }
        )

    return result
