from typing import Dict

import time
import os
import subprocess

import datetime
from urllib.parse import urlparse, parse_qs

import requests

from bs4 import BeautifulSoup
from database import SessionLocal

from models import Regulation
class RegulationPost:
    def __init__(self, post_type, post_title, post_create_date, post_file_url, post_enforce_date, post_next_link) -> None:
        self.type = post_type
        self.title = post_title
        self.create_date = post_create_date
        self.file_url = post_file_url
        self.enforce_date = post_enforce_date
        self.next_link = post_next_link

class RegulationCrawler:
    base_url = "http://www.humetro.busan.kr"
    target_boards = [
        "/homepage/default/board/list.do?conf_no=105&board_no=&category_cd=&menu_no=1001060302",
        "/homepage/default/board/list.do?conf_no=107&board_no=&category_cd=&menu_no=1001060303",
        "/homepage/default/board/list.do?conf_no=106&board_no=&category_cd=&menu_no=1001060301",
    ]

    db = SessionLocal()

    def __init__(self) -> None:
        self.current_post_info: Dict | None = dict()

    def handle_post(self, post_link) -> RegulationPost:
        post_html = requests.get(self.base_url + post_link)
        post_soup = BeautifulSoup(post_html.content, 'lxml')
        post_text = post_soup.select_one('div.board-view-title').text

        next_post_link_elem = post_soup.select_one('li.li-prev a')
        post_next_link = next_post_link_elem.get('href') if next_post_link_elem else None
        
        # error handling for edge case
        if '정관' in post_text:
            post_text = '정관' + post_text
        elif '조례' in post_text:
            post_text = '조례' + post_text

        post_info_list = [i.strip() for i in post_text.replace('\t','').split('\n') if i.strip() != '']
        post_type = post_info_list[0].replace('[', '').replace(']', '')
        post_title = post_info_list[1]

        # error handling for edge case
        if '[내규]' in post_title:
            post_type = '내규'
            post_title.replace('[내규]', '')

        post_create_date = datetime.datetime.strptime(post_info_list[3], '%Y-%m-%d')
        print('Processing ', post_type, post_title,)
        try:
            post_file_url = post_soup.select_one('ul.board-view-filelist a').get('href')
        except:
            post_file_url = None

        try:
            post_enforce_date_text = post_soup.select_one('div#boardContents').text.strip().split(':')[1].strip().replace(' ', '')
            post_enforce_date = datetime.datetime.strptime(post_enforce_date_text, '%Y년%m월%d일')
        except Exception as e:
            post_enforce_date = None
        return RegulationPost(post_type, post_title, post_create_date, post_file_url, post_enforce_date, post_next_link)

    def crawl(self) -> None:
        try:
            for board in self.target_boards:
                board_html = requests.get(self.base_url + board)
                board_soup = BeautifulSoup(board_html.content, 'lxml')
                # 첫 번째 글을 무조건 클릭한다.
                first_post = board_soup.select('table.basic-list-table tbody tr')[0]
                next_link = first_post.select_one('a').get('href')

                while next_link:
                    post = self.handle_post(next_link)

                    regulation = self.db.query(Regulation).filter_by(
                        title = post.title,
                        type = post.type
                    ).first()

                    if not regulation:
                        print(post.title, 'not exists!')
                        regulation = Regulation(
                            title = post.title,
                            type = post.type,
                            create_date = post.create_date,
                            update_date = post.create_date,
                            enforce_date = post.enforce_date,
                            file_url = post.file_url,
                            html_url = None,
                        )
                        self.db.add(regulation)
                        self.db.commit()
                    elif regulation.create_date < post.create_date:
                        print(post.title, 'exists!, but outdated')
                        regulation.create_date = post.create_date
                        regulation.update_date = post.create_date
                        regulation.enforce_date = post.enforce_date
                        regulation.file_url = post.file_url
                        regulation.html_url = None
                        self.db.commit()
                    else:
                        print(post.title, 'same or newer version exists!, skipping')
                    next_link = post.next_link
        finally:
            self.db.close()
    
    def handle_file_process(self) -> None:
        """
        1. db를 조회한다.
        2. html_url이 없는 로우를 대상으로
        3. db에 저장된 url에서 파일을 다운받는다.
        4. 다운로드된 파일은 os.system이나 subprocess 호출로 html로 변환한다.
        5. 다운로드된 파일을 지운다.
        6. 모든 과정이 성공하면 db에 html_url을 지정한다.
        """
        targets = self.db.query(Regulation).filter_by(
            html_url = None
        ).all()

        if subprocess.run(['hwp5html', '--version']).returncode != 0:
            raise Exception('hwp5html is not installed')

        for target in targets:
            print('File Processing : ', target.title)
            try:
                self.download_file(target)
                self.convert_file_to_html(target)
                # self.remove_file(target)
            except Exception as e:
                print(e)
                pass
            # else:
            #     # self.update_html_url(target)
            # finally:
            #     self.db.close()
            

    def check_file_exists(self) -> None:
        pass
    
    def download_file(self, target: Regulation) -> None:
        file_ext = parse_qs(urlparse(target.file_url).query).get('file_name_origin')[0].split('.')[-1].lower()
        filename = f'[{target.type}]{target.title.replace(" ", "")}_{target.create_date.date()}.{file_ext}' 
        print('File downloading : ', filename)
        with open('miscs/' + filename, 'wb') as f:
            res = requests.get(self.base_url + target.file_url)
            f.write(res.content)
        time.sleep(1)
    
    def update_html_url(self, target:Regulation) -> None:
        target.html_url = ""
        self.db.commit()
        pass
    
    def convert_file_to_html(self, target: Regulation) -> None:
        file_ext = parse_qs(urlparse(target.file_url).query).get('file_name_origin')[0].split('.')[-1].lower()
        filename = f'[{target.type}]{target.title.replace(" ", "")}_{target.create_date.date()}.{file_ext}' 
        file_dir = os.path.join(os.getcwd(), 'miscs')
        file_path = os.path.join(file_dir, filename)
        hwp_dest = os.path.join(os.getcwd(), 'assets', 'html', '_regulation', filename.replace('.hwp', ''))
        pdf_dest = os.path.join(os.getcwd(), 'assets', 'html', '_regulation', filename.replace('.pdf', ''))
        print('File converting : ', filename)
        if 'hwp' in file_ext:
            result = subprocess.run(['hwp5html', '--output', hwp_dest, file_path])
        elif 'pdf' in file_ext:
            """
                1. 도커가 설치되어 있는지 확인한다.
                2. 도커 이미지를 풀링한다.
                3. 도커 풀된 도커 이미지를 바탕으로 커맨드를 실행한다.
            """
            print('pdf')
            result = subprocess.run(
                [
                   'docker',
                   'run',
                   '-ti',
                   '--rm',
                   '-v',
                   f'{file_dir}/:/pdf',
                   '-w',
                   '/pdf',
                   'pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-alpine-3.12.0-x86_64',
                   '--dest-dir',
                   pdf_dest,
                   '--zoom',
                   '1.3',
                    filename,
                ]
            )
            result = ""
        if result.returncode != 0:
            raise Exception(f'{filename} 이 정상 변환되지 않았습니다.')


if __name__ == "__main__":
    crawler = RegulationCrawler()
    # crawler.crawl()
    crawler.handle_file_process()