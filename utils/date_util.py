import datetime

def get_next_monday(dt: datetime.datetime) -> datetime.datetime:
    return get_last_monday(dt) + datetime.timedelta(days=7)

def get_last_monday(dt: datetime.datetime) -> datetime.datetime:
    while dt.weekday() != 0:
        dt -= datetime.timedelta(days=1)
    return dt