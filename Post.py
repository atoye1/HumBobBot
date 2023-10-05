import datetime

from utils.date_util import get_next_monday


class Post:
    def __init__(self, title, created_at):
        self.title = title
        #2023.10.22  like string
        self.created_at = datetime.datetime.strptime(created_at, '%Y.%m.%d')
        self.create_date = created_at[2:].replace('.','')
        self.url = None
        self.image_url = None
        self.target_date = get_next_monday(self.created_at)

    @property
    def is_diet(self):
        if '식단표' in self.title:
            return True
        return False

