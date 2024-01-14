import datetime
import re

def extract_date_from_title(title: str):
    date_patterns = [
        r"\b(?:20\d{2}/)?\d{1,2}/\d{1,2}\b",
        r"\b\d{4}/\d{1,2}/\d{1,2}\b",  # YYYY/MM/DD
        r"\b\d{1,2}/\d{1,2}\b",        # MM/DD
        r"\b\d{1,2}\.\d{1,2}\b",        # MM.DD
        r"\b\d{4}-\d{1,2}-\d{1,2}\b",  # YYYY-MM-DD
        r"\b\d{1,2}-\d{1,2}\b",  # MM-DD
        r"\b\d{1,2}월\s?\d{1,2}일\b",
    ]

    date_regex = re.compile("|".join(date_patterns))
    extracted_dates = date_regex.findall(title)

    extracted_dates = [        date.replace(".", "/").replace("-", "/").replace("월", "/").replace("일", "").replace(" ", "")
        for date in extracted_dates
    ]

    if not extracted_dates:
        return None

    datetime_list = []
    year = datetime.datetime.now().year
    for date in extracted_dates:
        splitted_date = date.split('/')
        if len(splitted_date) == 3:
            splitted_date = splitted_date[1:]
        month, day = splitted_date
        datetime_list.append(datetime.datetime(year, int(month), int(day)))
    datetime_list.sort()

    return datetime_list[0]
    

# Test the function with an example
test_data = ["본사 구내식당 주간식단표(1/2~1/5)&신정 휴무(1/1)",
"신평차량사업소 구내식당 주간식단표(1/1~1/7)",
"신평차량사업소 구내식당 주간식단표(1월1일 ~ 1월 7일)",
"노포차량기지 구내식당 주간식단표(2024/1/1~1/7)",
"경전철운영사업소 구내식당 주간 식단표(1/1~1/7)",
"♡ 호포 구내식당 주간식단표(1/1~7)",
"경전철운영사업소 구내식당 주간 식단표(12/25~12/31)",
"대저차량기지 구내식당 주간식단표(12/25~12/31)",
"본사 구내식당 주간식단표(12/26~12/29) & 크리스마스 휴무(12/25)",
"신평차량사업소 구내식당 주간식단표(12/25~12/31)",
"노포차량기지 구내식당 주간식단표(12/25~12/31)",
"★ 광안분소동 구내식당 주간식단표(12.25~12.31)",
"♡ 호포 구내식당 주간식단표(12/25~31)",
"★ 광안분소동 구내식당 주간식단표(12.18~12.24)",
"노포차량기지 구내식당 주간식단표(12/18~12/24)",
"대저차량기지 구내식당 주간식단표(12/18~12/24)",
"본사 구내식당 주간식단표(12/18~12/22)",
"♡ 호포 구내식당 주간식단표(12/18~24)",
"♡ 호포 구내식당 주간식단표(12월 17일부터 23일까지)",
"신평차량사업소 구내식당 주간식단표(12/18~12/24)",]

for data in test_data:
    print(extract_date_from_title(data))
