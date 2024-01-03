import base64
import os
import json
import requests
import time
import sys
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException

load_dotenv()

btcep_id = os.getenv('BTCEP_ID')
btcep_pw = os.getenv('BTCEP_PW')


class DietCrawler:
    def __init__(self, btcep_id, btcep_pw):
        self.driver = None
        self.main_url = 'https://btcep.humetro.busan.kr'
        self.menu_url = 'https://btcep.humetro.busan.kr/portal/default/main/eboard/eMenu'
        self.btcep_id = btcep_id
        self.btcep_pw = btcep_pw
        self.posts = None
        self.post_idx = 0
        pass

    def setup_webdriver(self, headless=True):
        if self.driver is not None:
            return

        options = Options()
        options.add_argument('--start-maximzed')
        if headless:
            options.add_argument('-headless')

        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)

    def _navigate_to_main(self):
        self.driver.get(self.main_url)
        pass

    def _navigate_to_menu_board(self):
        self.driver.get(self.menu_url)
        time.sleep(3)

    def _login(self):
        self.driver.find_element(By.ID, 'userId').send_keys(self.btcep_id)
        self.driver.find_element(By.ID, 'password').send_keys(self.btcep_pw)
        self.driver.find_element(By.CSS_SELECTOR, 'a.btn_login').click()
        self.driver.find_element(
            By.CSS_SELECTOR, 'input#certi_num').send_keys(self.btcep_id)

        self.driver.execute_script('login()')
        time.sleep(5)
        pass

    def _change_iframe(self):
        self.driver.switch_to.default_content()
        table_frame = self.driver.find_element(By.CSS_SELECTOR, 'iframe')
        self.driver.switch_to.frame(table_frame)

    def _fetch_posts(self):
        board_el = self.driver.find_element(By.CSS_SELECTOR, 'form#boardList')
        self.posts = board_el.find_elements(By.CSS_SELECTOR, 'tbody tr')
        pass

    def _save_image(self):
        pass

    def _post_to_server(self, post_data):
        post_endpoint = 'http://130.162.153.197:8000/diet/upload'
        # Image to send
        files = {
            "upload_file": ('upload_file.jpg', post_data.get('image_content'), 'image/jpeg'),
        }
        post_create_date = post_data.get('post_created_at').replace('.', '')

        if len(post_create_date) > 6:
            post_create_date = post_create_date[2:]

        post_response = requests.post(post_endpoint,
                                      data={
                                          'post_title': post_data.get('post_title'),
                                          'post_create_date': post_create_date},
                                      files=files)
        print(f'Uploading : {post_data.get('post_title')}')
        print('Upload result : ', json.loads(post_response.content))

        pass

    def _extract_image(self, image_url):
        if image_url is None:
            raise ValueError("Image URL MUST not None!!!")

        if 'data:image/png;base64' in image_url:
            image_content = base64.b64decode(
                self.image_url.split(',')[1].strip())
        else:
            response = requests.get(image_url)
        # ToDo url이 아니라 base64 인코딩된 이미지 자체가 입력으로 들어온 경우 처리하기
            if response.status_code != 200:
                raise Exception('Failed to retrieve the file')
            image_content = response.content

        return image_content

    def _process_single_post(self, post):
        self._change_iframe()

        post_data = {
            'post_title': post.find_element(By.CSS_SELECTOR, 'td.L a').text,
            'post_id': post.find_element(By.CSS_SELECTOR, 'td.L a').get_attribute('id'),
            'post_created_at': post.find_elements(By.CSS_SELECTOR, 'td.C')[-2].text,
            'image_url': None,
            'image_content': None,
        }

        if '식단표' not in post_data.get('post_title'):
            return

        post_script = f"ebList.readBulletin('eMenu','{
            post_data.get('post_id')}');"
        self.driver.execute_script(post_script)
        time.sleep(3)

        post_data['image_url'] = self.driver.find_element(
            By.CSS_SELECTOR, 'img').get_attribute('src')
        post_data['image_content'] = self._extract_image(
            post_data['image_url'])

        self._post_to_server(post_data)

    def crawl(self):
        self._navigate_to_main()
        self._login()
        self._navigate_to_menu_board()
        self._change_iframe()
        self._fetch_posts()

        # Implement this logic to avoid stale elem Exception
        while self.post_idx < len(self.posts) - 1:
            self._navigate_to_menu_board()
            self._change_iframe()
            self._fetch_posts()
            try:
                self._process_single_post(self.posts[self.post_idx])
            except NoSuchElementException:
                pass
            self.post_idx += 1

    def quit(self):
        self.driver.quit()

    @staticmethod
    def is_menu_post(title: str) -> bool:
        return '식단표' in title


if __name__ == "__main__":
    crawler = DietCrawler(btcep_id, btcep_pw,)
    crawler.setup_webdriver(headless=False)
    crawler.crawl()
    crawler.quit()
    sys.exit(0)
