from datetime import datetime, timezone, timedelta

####
## Reference time, in our time zone
now = datetime.now()
date_format = '%Y-%m-%d %H:%M:%S'

## Grace period
grace = timedelta(days=5)

def is_unsubmitted(x):
    return x['Status'] == 'Missing' or x['Total Score'] is None or x['Total Score'] < x['Max Points'] / 2.0 

def is_overdue(x, due):
    return is_unsubmitted(x) and due < now + grace

def is_near_due(x, due):
    return is_unsubmitted(x) and (due - now) < timedelta(days = 2) and not is_overdue(x, due)# now < due + timedelta(days=5)

def is_submitted(x):
    return x['Status'] != 'Missing'


