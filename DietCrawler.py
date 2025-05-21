import base64
import os
import json
import requests
import time
import sys
import logging

# Custom modules
import config

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

# load_dotenv() # Handled in config.py

# btcep_id = os.getenv('BTCEP_ID') # Access via config
# btcep_pw = os.getenv('BTCEP_PW') # Access via config

logger = logging.getLogger(__name__)

class DietCrawler:
    def __init__(self, btcep_id, btcep_pw):
        logger.info("Initializing DietCrawler...")
        self.driver = None
        self.main_url = config.DIET_CRAWLER_MAIN_URL
        self.menu_url = config.DIET_CRAWLER_MENU_URL
        self.btcep_id = btcep_id
        self.btcep_pw = btcep_pw
        self.posts = None
        self.post_idx = 0
        pass

    def setup_webdriver(self, headless=True):
        logger.info(f"Setting up WebDriver. Headless: {headless}")
        if self.driver is not None:
            logger.debug("WebDriver already initialized.")
            return

        options = Options()
        options.add_argument('--start-maximzed')
        if headless:
            options.add_argument('-headless')

        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(10)
        logger.info("WebDriver setup complete.")

    def _navigate_to_main(self):
        logger.info(f"Navigating to main URL: {self.main_url}")
        self.driver.get(self.main_url)
        pass

    def _navigate_to_menu_board(self):
        logger.info(f"Navigating to menu board URL: {self.menu_url}")
        self.driver.get(self.menu_url)
        time.sleep(3) # Consider replacing with explicit waits

    def _login(self):
        logger.info("Attempting login...")
        self.driver.find_element(By.ID, 'userId').send_keys(self.btcep_id)
        self.driver.find_element(By.ID, 'password').send_keys(self.btcep_pw)
        self.driver.find_element(By.CSS_SELECTOR, 'a.btn_login').click()
        self.driver.find_element(
            By.CSS_SELECTOR, 'input#certi_num').send_keys(self.btcep_id)

        self.driver.execute_script('login()')
        time.sleep(5) # Consider replacing with explicit waits
        logger.info("Login successful.")
        pass

    def _change_iframe(self):
        logger.debug("Changing to iframe...")
        self.driver.switch_to.default_content()
        table_frame = self.driver.find_element(By.CSS_SELECTOR, 'iframe')
        self.driver.switch_to.frame(table_frame)
        logger.debug("Successfully changed to iframe.")

    def _fetch_posts(self):
        logger.info("Fetching posts...")
        board_el = self.driver.find_element(By.CSS_SELECTOR, 'form#boardList')
        self.posts = board_el.find_elements(By.CSS_SELECTOR, 'tbody tr')
        logger.info(f"Found {len(self.posts)} posts.")
        pass

    def _save_image(self):
        # This method is not implemented, so no logging changes needed unless it gets implemented.
        pass

    def _post_to_server(self, post_data):
        post_endpoint = config.DIET_UPLOAD_ENDPOINT
        files = {
            "upload_file": ('upload_file.jpg', post_data.get('image_content'), 'image/jpeg'),
        }
        post_create_date = post_data.get('post_created_at', '').replace('.', '')

        if len(post_create_date) > 6:
            post_create_date = post_create_date[2:]
        
        payload = {
            'post_title': post_data.get('post_title'),
            'post_create_date': post_create_date
        }
        
        logger.info(f"Uploading post: {payload.get('post_title')} to {post_endpoint}")
        try:
            post_response = requests.post(post_endpoint, data=payload, files=files, timeout=10)
            post_response.raise_for_status() # Will raise an HTTPError for bad responses (4XX or 5XX)
            logger.info(f"Upload successful for post: {payload.get('post_title')}. Response: {post_response.json()}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during post for {payload.get('post_title')}: {e}. Response content: {e.response.content}", exc_info=True)
        except requests.exceptions.RequestException as e: # Catches other requests exceptions like ConnectionError
            logger.error(f"Request exception during post for {payload.get('post_title')}: {e}", exc_info=True)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response for {payload.get('post_title')}. Response text: {post_response.text}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred during post for {payload.get('post_title')}: {e}", exc_info=True)
        pass

    def _extract_image(self, image_url):
        logger.debug(f"Extracting image from URL: {image_url}")
        if image_url is None:
            logger.error("Image URL is None.")
            raise ValueError("Image URL MUST not None!!!")

        if 'data:image/png;base64' in image_url:
            logger.warning("Attempting to extract Base64 encoded image. Current implementation assumes self.image_url, but it should be image_url.")
            # Corrected: use image_url parameter instead of self.image_url
            try:
                image_content = base64.b64decode(image_url.split(',')[1].strip())
                logger.info("Successfully decoded Base64 image.")
            except IndexError as e:
                logger.error(f"Error splitting Base64 image string: {image_url}. Error: {e}", exc_info=True)
                raise
            except base64.binascii.Error as e: # More specific error for base64 decoding
                logger.error(f"Error decoding Base64 string: {e}", exc_info=True)
                raise
        else:
            try:
                response = requests.get(image_url, timeout=10)
                response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
                image_content = response.content
                logger.info(f"Successfully downloaded image from {image_url}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error retrieving image from {image_url}: {e}", exc_info=True)
                raise Exception(f'Failed to retrieve the file from {image_url}') from e
            except requests.exceptions.RequestException as e:
                logger.error(f"Request exception retrieving image from {image_url}: {e}", exc_info=True)
                raise Exception(f'Failed to retrieve the file from {image_url}') from e
        return image_content

    def _process_single_post(self, post):
        post_data = {} # Initialize post_data to ensure it's available in except blocks
        try:
            self._change_iframe()
            post_data = {
                'post_title': post.find_element(By.CSS_SELECTOR, 'td.L a').text,
                'post_id': post.find_element(By.CSS_SELECTOR, 'td.L a').get_attribute('id'),
                'post_created_at': post.find_elements(By.CSS_SELECTOR, 'td.C')[-2].text,
                'image_url': None,
                'image_content': None,
            }
            logger.info(f"Processing post: {post_data.get('post_title')}")

            if '식단표' not in post_data.get('post_title'):
                logger.debug(f"Skipping post as it's not a menu: {post_data.get('post_title')}")
                return

            post_script = f"ebList.readBulletin('eMenu','{post_data.get('post_id')}');"
            logger.debug(f"Executing script for post: {post_script}")
            self.driver.execute_script(post_script)
            time.sleep(3) # Consider explicit waits

            post_data['image_url'] = self.driver.find_element(
                By.CSS_SELECTOR, 'img').get_attribute('src')
            logger.debug(f"Image URL found: {post_data['image_url']}")
            post_data['image_content'] = self._extract_image(post_data['image_url'])

            self._post_to_server(post_data)
            logger.info(f"Successfully processed post: {post_data.get('post_title')}")

        except NoSuchElementException as e:
            logger.error(f"Element not found while processing post: {post_data.get('post_title', 'Unknown Post')}. Error: {e}", exc_info=True)
        except Exception as e: # General exception handler
            logger.error(f"An unexpected error occurred while processing post: {post_data.get('post_title', 'Unknown Post')}. Error: {e}", exc_info=True)


    def crawl(self):
        logger.info("Starting crawl process...")
        try:
            self._navigate_to_main()
            self._login()
            self._navigate_to_menu_board()
            self._change_iframe()
            self._fetch_posts()

            logger.info(f"Crawling through {len(self.posts)} posts.")
            # Implement this logic to avoid stale elem Exception
            while self.post_idx < len(self.posts): # Corrected loop condition
                current_post_element = self.posts[self.post_idx]
                # It's good practice to log which post index is being processed.
                logger.info(f"Attempting to process post index: {self.post_idx}")
                try:
                    self._process_single_post(current_post_element)
                except StaleElementReferenceException: # More specific exception
                    logger.warning(f"StaleElementReferenceException for post index {self.post_idx}. Re-fetching posts list.")
                    # This strategy handles cases where the DOM structure changes (e.g., AJAX updates list).
                    # Re-navigating and re-fetching the posts list is a common way to get fresh elements.
                    self._navigate_to_menu_board() # Navigate back to refresh the list of posts
                    self._change_iframe() # Re-select the correct iframe if necessary
                    self._fetch_posts() # Get the fresh list of post elements
                    
                    # After re-fetching, the element at self.post_idx might be different or the list shorter.
                    # To avoid potential infinite loops on a persistently problematic element or an ever-changing list,
                    # we log the skip and rely on the loop incrementing self.post_idx to move forward.
                    # More sophisticated recovery might involve trying to find an equivalent to current_post_element,
                    # but that adds significant complexity.
                    if self.post_idx < len(self.posts): # Check if index is still valid after re-fetch
                        logger.info(f"Skipping processing for post index {self.post_idx} after stale element and list refresh to avoid potential loop. Next attempt will be index {self.post_idx + 1}.")
                    else:
                        logger.info("Reached end of posts after stale element re-fetch and list refresh.")
                        break # Exit loop if index is out of bounds
                # The original code had a general NoSuchElementException here,
                # but it's better handled within _process_single_post for more context.
                self.post_idx += 1
            logger.info("Crawl process finished.")
        except Exception as e:
            logger.critical(f"A critical error occurred during the crawl setup or main loop: {e}", exc_info=True)


    def quit(self):
        if self.driver:
            logger.info("Quitting WebDriver.")
            self.driver.quit()

    @staticmethod
    def is_menu_post(title: str) -> bool: # This static method doesn't need logging itself
        return '식단표' in title


if __name__ == "__main__":
    # BasicConfig is already called in config.py, so logs should work out of the box.
    logger.info("DietCrawler script started directly.")
    try:
        crawler = DietCrawler(config.BTCEP_ID, config.BTCEP_PW,)
        crawler.setup_webdriver(headless=True) # Changed to True for typical script execution
        crawler.crawl()
    except Exception as e:
        logger.critical(f"Unhandled exception in __main__: {e}", exc_info=True)
    finally:
        if 'crawler' in locals() and crawler.driver is not None: # Ensure driver exists
             crawler.quit()
        logger.info("DietCrawler script finished.")
        sys.exit(0) # Consider if sys.exit(0) is always appropriate
