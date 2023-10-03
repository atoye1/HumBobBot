import datetime

def get_next_monday(dt: datetime.datetime) -> datetime.datetime:
    # Calculate days until next Monday (1 represents Tuesday in .weekday())
    days_until_next_monday = (7 - dt.weekday()) % 7 or 7
    next_monday_date = dt + datetime.timedelta(days=days_until_next_monday)
    return next_monday_date

def get_previous_monday(dt: datetime.datetime) -> datetime.datetime:
    while dt.weekday() != 0:
        dt -= datetime.timedelta(days=1)
    return dt