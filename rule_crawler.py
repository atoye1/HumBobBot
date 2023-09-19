import requests
import json
import re
from bs4 import BeautifulSoup

init_url = "http://www.humetro.busan.kr/homepage/default/board/view.do?board_no=2309XUAL2X&conf_no=106&menu_no=1001060301&c_page=1&geulmeori=&search_key=&keyword="
base_url = "http://www.humetro.busan.kr"
target_url = init_url

rules = []

duplicate = False
while True:
    html = requests.get(target_url)
    soup = BeautifulSoup(html.content, 'lxml')
    rule_title = soup.select_one('div.board-view-title h3.bv-tit').text.strip()
    pattern = '\d{4}-\d{2}-\d{2}'
    created_at_el = soup.select_one('div.board-view-title')
    created_at_text = created_at_el.text
    created_at_text = re.search(pattern, created_at_text)[0]

    file_url_el = soup.select_one('ul.board-view-filelist li a')
    file_url_text = file_url_el.get('href')
    file_url_text = base_url + file_url_text

    next_link_el = soup.select_one('li.li-prev a')
    if next_link_el is None:
        print('no next link!! terminating!!')
        break

    next_link_text = next_link_el.get('href')
    next_link_text = base_url + next_link_text

    print(rule_title)
    print(created_at_text)
    print(file_url_text)
    print(next_link_text)

    for rule in rules:
        if rule_title == rule.get('title'):
            duplicate = True
            break

    if not duplicate:
        rules.append({
            "title":rule_title,
            "created_at":created_at_text,
            "file_url": file_url_text,
        })

    target_url = next_link_text
    duplicate = False

with open('rules.json', 'w') as f:
    json.dump(rules, f, indent=4, ensure_ascii=False)