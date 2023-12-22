from datetime import datetime, timezone, timedelta
import pandas as pd

####
## Reference time, in our time zone
now = datetime.now()
date_format = '%Y-%m-%d %H:%M:%S'
timezone = datetime.now().astimezone().tzinfo
due_date = 'Due ({})'.format(timezone)

## Grace period
grace = timedelta(days=5)

def is_unsubmitted(x):
    return x['Status'] == 'Missing' or x['Total Score'] is None or x['Total Score'] < x['Max Points'] / 2.0 

def is_overdue(x, due):
    if not pd.isnull(x[due_date]):
        due = x[due_date]
    return is_unsubmitted(x) and due < now + grace

def is_near_due(x, due):
    if not pd.isnull(x[due_date]):
        due = x[due_date]

    return is_unsubmitted(x) and (due - now) < timedelta(days = 2) and not is_overdue(x, due)# now < due + timedelta(days=5)

def is_submitted(x: pd.Series):
    return x['Status'] != 'Missing'

def is_below_mean(x: pd.Series, mean: float):
    return x['Total Score'] < mean

def is_far_below_mean(x: pd.Series, mean: float):
    return x['Total Score'] < mean/3

def row_test(row: pd.Series, due: datetime, mean: float, median: int, min: int, max: int, stdev: float, row_test_fn) -> str:
    return eval(row_test_fn)