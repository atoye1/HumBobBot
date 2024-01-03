import os
import requests
import datetime
import time
import re
import sys
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options

from Post import Post
from Diet import Diet

class DietCrawler:
    def __init__(self, driver, btcep_id, btcep_pw):
        self.driver = driver
        self.menu_url = "https://btcep.humetro.busan.kr/portal/default/main/eboard/eMenu"
        self.btcep_id = btcep_id
        self.btcep_pw = btcep_pw
        pass

    def _navigate_to_btcep(self):    
        pass
    
    def _login(self):
        pass

    def _change_iframe(self):
        pass

    def _fetch_posts(self):
        pass
    
    def _save_image(self):
        pass

    def _post_to_server(self):
        pass
    
    def crawl(self):
        self._navigate_to_btcep()
        self._login()
        self._change_iframe()
        for i in range(10):
            if not DietCrawler.is_menu_post('abc'):
                continue
            self._save_image()
            self._post_to_server()
        pass

    @staticmethod
    def is_menu_post(title: str) -> bool:
        return '식단표' in title
    
    
load_dotenv()

btcep_id = os.getenv('BTCEP_ID')
btcep_pw = os.getenv('BTCEP_PW')


# Path to the GeckoDriver executable (replace with your actual path)
geckodriver_path = './geckodriver.exe'

# Create options for Firefox
options = Options()
options.add_argument('-headless') # Set headless mode to True
options.add_argument("--start-maximized")

# Initialize the WebDriver with the options
driver = webdriver.Firefox(options=options)

# Navigate to a website
driver.get('https://btcep.humetro.busan.kr/')
driver.implicitly_wait(10)
print(driver.title)

driver.find_element(By.ID, 'userId').send_keys(btcep_id)
driver.find_element(By.ID, 'password').send_keys(btcep_pw)
driver.find_element(By.CSS_SELECTOR, 'a.btn_login').click()
driver.find_element(By.CSS_SELECTOR, 'input#certi_num').send_keys(btcep_id)

driver.execute_script('login()')
time.sleep(5)


def change_frame():
    driver.switch_to.default_content()
    table_frame = driver.find_element(By.CSS_SELECTOR, 'iframe')
    driver.switch_to.frame(table_frame)

def change_pagesize_to_40():
    # interact with select options
    page_size = driver.find_element(By.ID, 'pageSize')
    select = Select(page_size)
    select.select_by_index(3)

def parse_date_from_title(date_string):
    pattern = r'\((\d+)/(\d+)~(\d+)\/?(\d+)?\)'
    # pattern = r'(\d{1,2}/\d{1,2}(?:\s*~\s*\d{1,2}/\d{1,2})?)'
    match = re.search(pattern, date_string)

    if match:
        print(match.groups())
        start_month, start_day, end_month, end_day = match.groups()
        if end_day is None:
            end_day = end_month
            end_month = start_month

        # 현재 연도를 가져오거나, 필요한 연도 정보를 직접 제공합니다
        current_year = datetime.datetime.now().year

        # datetime 객체 생성
        start_date = datetime.datetime(current_year, int(start_month), int(start_day))
        end_date = datetime.datetime(current_year, int(end_month), int(end_day))

        print("시작 날짜:", start_date)
        print("종료 날짜:", end_date)
        return start_date, end_date
    else:
        raise Exception("날짜 형식이 올바르지 않습니다.")

def parse_loc_from_title(title):
    location = None
    locations = ['본사', '신평', '대저', '노포', '호포', '경전철', '광안']
    for loc in locations:
        if loc in title:
            location = loc
    # 날짜를 파싱
    if location is None:
        raise Exception("식당명을 찾을 수 없습니다.")
    return loc

def save_image(title, image_url):
    response = requests.get(image_url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Specify the local file path where you want to save the image
        local_image_path = f'{title}-{int(time.time())}.jpg'  # Change the filename and extension as needed

        # Save the image to the local file
        with open(local_image_path, 'wb') as image_file:
            image_file.write(response.content)

        print(f"Image downloaded to {local_image_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")

def sanitize_filename(filename):
    # Define a regular expression pattern for invalid characters in Windows filenames
    # This pattern matches any character that is not a letter, number, underscore, hyphen, or period
    invalid_char_pattern = r'[^\w\-.]'

    # Use re.sub to replace invalid characters with an empty string
    sanitized_filename = re.sub(invalid_char_pattern, '', filename)

    return sanitized_filename
    
menu_url = "https://btcep.humetro.busan.kr/portal/default/main/eboard/eMenu"
# driver.get(menu_url)
# change_frame()

for i in range(19, -1, -1):
    try:
        driver.get(menu_url)
        time.sleep(3)
        change_frame()
        board_el = driver.find_element(By.CSS_SELECTOR, 'form#boardList')
        pages = board_el.find_elements(By.CSS_SELECTOR, 'tbody tr td.L a')
        pages = board_el.find_elements(By.CSS_SELECTOR, 'tbody tr')
        page = pages[i]
        title = page.find_element(By.CSS_SELECTOR, 'td.L a').text
        page_id = page.find_element(By.CSS_SELECTOR, 'td.L a').get_attribute('id')
        page_script = f"ebList.readBulletin('eMenu','{page_id}');"
        page_created_at = page.find_elements(By.CSS_SELECTOR, 'td.C')[-2].text
        print('Processing : ', title)
        post = Post(title, page_created_at)
        print(post.title, post.create_date)
        if post.is_diet:
            driver.execute_script(page_script)
            time.sleep(3)
            try:
                diet = Diet(post)
                diet.image_url = driver.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                print(diet.image_url)
                err_count = 5
                while err_count and 'icon_new' in diet.image_url:
                    err_count -= 1
                    driver.execute_script("window.scrollBy(0, 500);")
                    print(f'error, retrying {err_count}')
                    driver.execute_script(page_script)
                    time.sleep(3)
                    diet = Diet(post)
                    diet.image_url = driver.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                diet.upload_image_to_server()
            except NoSuchElementException:
                print('element not found - ', title)
    except Exception as e:
        print(f'below exception raised while handling {title}')
        print(e)

driver.quit()
sys.exit(0)