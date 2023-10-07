import requests
import json
import re
from bs4 import BeautifulSoup
from database import SessionLocal
from models import Regulation

class RegulationCrawler:
    target_boards = [
        "http://www.humetro.busan.kr/homepage/default/board/list.do?conf_no=106&board_no=&category_cd=&menu_no=1001060301",
        "http://www.humetro.busan.kr/homepage/default/board/list.do?conf_no=105&board_no=&category_cd=&menu_no=1001060302",
        "http://www.humetro.busan.kr/homepage/default/board/list.do?conf_no=107&board_no=&category_cd=&menu_no=1001060303"
    ]

    db = SessionLocal()

    def __init__(self) -> None:
        pass

    def crawl(self) -> None:
        for board in self.target_boards:
            """
            1. get lists,
            2. access individual posts
            3. db commit, file download, convert
            """
            board_html = requests.get(board)
            board_soup = BeautifulSoup(html.content, 'lxml')
            # 첫 번째 글을 무조건 클릭한다.
            first_post = board_soup.select('table.basic-list-table tbody tr')[0]
            first_post_link = first_post.select_one('a').get('href')

            post_html = requests.get(first_post_link)
            post_soup = BeautifulSoup(html, 'lxml')
            while True:
                regulation_title = post_soup.select()
                regulation_type
                enforce_date
                file_url
                html_url
                self.db.Query(Regulation)

                # 포스트가 없거나, db에 현재 포스트의 내용이 저장된 경우 break한다.

            rule_title = soup.select_one('div.board-view-title h3.bv-tit').text.strip()
            pattern = '\d{4}-\d{2}-\d{2}'
            created_at_el = soup.select_one('div.board-view-title')
            created_at_text = created_at_el.text
            created_at_text = re.search(pattern, created_at_text)[0]
            break
        pass
    
    def check_exists(self) -> None:
        pass
    
    def download_file(self) -> None:
        pass
    
    def convert_file_to_html(self) -> None:
        pass

if __name__ == "__main__":
    crawler = RegulationCrawler()
    crawler.crawl()
    

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