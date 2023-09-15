import datetime

from utils import get_next_monday


class Post:
    def __init__(self, title):
        self.title = title
        self.created_at = datetime.datetime.now()
        self.url = None
        self.image_url = None
        self.target_date = get_next_monday(self.created_at)

    @property
    def is_diet(self):
        if '식단표' in self.title:
            return True
        return False
