import datetime
import re
import requests
import json
import base64

from Post import Post


class Diet:
    def __init__(self, post: Post):
        self.post = post
        self.title = post.title
        self.image_url = None
        self.post_url = "http://130.162.153.197:8000/upload_diet/"
        self.yymmdd = self.start_date.strftime('%y%m%d')

    @property
    def start_date(self) -> datetime.datetime | None:

        def get_last_monday(dt: datetime.datetime) -> datetime.datetime:
            """
            Returns the datetime of the given date if it's a Monday, 
            otherwise returns the datetime of the previous Monday.
            """
            while dt.weekday() != 0:  # 0 represents Monday in the weekday system
                dt -= datetime.timedelta(days=1)
            return dt


        def get_next_monday_year() -> str:
            today = datetime.datetime.now()
            days_unitl_next_monday = (0 - today.weekday() + 7) % 7
            next_monday = today + \
                datetime.timedelta(days=days_unitl_next_monday)
            next_monday_year = next_monday.year
            return next_monday_year

        pattern = r'(\d{1,2}/\d{1,2}(?:~\d{1,2}(?:/\d{1,2})?)?)'
        result = re.findall(pattern, self.title)
        if result:  # (9/11 ~ 9/17) pattern found
            date_string = result[0].split('~')[0]
            next_monday_year = get_next_monday_year()
            extracted_date = datetime.datetime.strptime(f'{next_monday_year}/{date_string}', '%Y/%m/%d').date()
            return get_last_monday(extracted_date)

        pattern = r"(\d+\.\d+~\d+\.\d+)" # pattern for 9.18~9.24
        result = re.findall(pattern, self.title)
        # 코드가 지저분하고 로직관리가 한곳에서 되지 않으니, 내가 쓴 코드를 내가 착각해서 버그를 못고침.
        # 분리하고, 책임을 나눠야한다.
        # 결국 return 은 한곳에서하고, get_last_monday도 스태틱메서드처럼 한곳에서 호출해야함.
        if result:
            date_string = result[0].split('~')[0]
            next_monday_year = get_next_monday_year()
            return get_last_monday(datetime.datetime.strptime(f'{next_monday_year}.{date_string}', '%Y.%m.%d').date())
        return self.post.target_date

    @property
    def location(self):
        candidates = ['본사', '노포', '신평', '호포', '광안', '대저', '경전철', '안평']
        for elem in candidates:
            if elem in self.title:
                return elem
        return None

    def upload_image_to_server(self):
        if self.image_url is None:
            raise TypeError('image_url should not None')
        
        if 'data:image/png;base64' in self.image_url:
            image_content = base64.b64decode(self.image_url.split(',')[1].strip()) 
        else:
            response = requests.get(self.image_url)
        #ToDo url이 아니라 base64 인코딩된 이미지 자체가 입력으로 들어온 경우 처리하기
            if response.status_code != 200:
                print("Failed to retrieve the file.")
                raise Exception('Failed to retrieve the file')
            image_content = response.content

        # Data to send
        data = {
            "yymmdd": self.yymmdd,  # Replace with your desired datetime
            "location": self.location  # Replace with your desired location
        }

        # Image to send
        files = {
            "filename": "test_filename.jpg",
            "file": image_content,
            "size": len(image_content),
            "headers": ""
        }

        post_response = requests.post(self.post_url, data=data, files=files)
        print(f'Uploading : {self.yymmdd}_{self.location}.jpg')

        print('Upload result : ', json.loads(post_response.content)['filename'])


if __name__ == "__main__":
    texts = [
        "신평차량사업소 구내식당 주간식단표(1/1~1/24)",
        "경전철운영사업소 구내식당 주간 식단표(9/18~9/24)",
        "본사 구내식당 식단변경 안내(9/14(목) 중식)",
        "노포차량기지 구내식당 주간식단표(9/18~9/24)",
        "★광안분소동 구내식당 주간 식단표(9/11~9/17)",
        "9월 본사 구내식당 특식데이 안내(9월 15일)",
        "본사 구내식당 주간식단표(9/11~9/15)(수정)",
        "대저차량기지 구내식당 주간식단표(9/11~9/17)(수정)",
        "노포차량기지 구내식당 주간식단표(9/11~9/17)",
        "신평차량사업소 구내식당 주간식단표(9/11~9/17)",
        "♡ 호포구내식당 주간식단표(9/11~17)",
        "경전철운영사업소 구내식당 주간 식단표(9/11~9/17)",
        "★광안분소동 구내식당 주간식단표",
        "경전철운영사업소 구내식당 주간 식단표(9/4~9/10)",
        "본사 구내식당 주간식단표(9/4~9/8)",
        "대저차량기지 구내식당 주간식단표(9/4~9/10)",
        "신평차량사업소 구내식당 주간식단표(9/4~9/10)",
        "☆★ 9월 호포 구내식당 이용직원 검수 참여 모니터링 신청 안내",
        "노포차량기지 구내식당 주간식단표(9/4~9/10)",
        "♡ 호포구내식당 주간식단표(9/4~10)"
    ]

    for text in texts:
        print('#' * 10)
        print(text)
        post = Post(text)
        if post.is_diet:
            test_diet = Diet(post)
            print(test_diet.location, test_diet.start_date, test_diet.yymmdd)
            print('\n')
        else:
            print(post.title, 'is not diet title')
