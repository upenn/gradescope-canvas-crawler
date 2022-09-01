from pyscope import pyscope as gs
from ics import Calendar, Event
import datetime
from getpass import getpass
import os

from pyscope.account import GSAccount

email = os.environ.get("GS_EMAIL")
pwd = os.environ.get("GS_PWD")

conn = gs.GSConnection()

# Login
if email is None or pwd is None:
    email = input("Email: ")
    pwd = getpass("Password: ")

print("Logging in...")
conn.login(email, pwd)

# Get Account
success = conn.get_account()
if not success:
    print("Failed to get account")
    exit(1)

acct: GSAccount = conn.account
course: gs.GSCourse = None

cal = Calendar()

for course in acct.student_courses.values():
    shortname = course.shortname
    print(f"Processing Course: {shortname}")

    event_size = datetime.timedelta(minutes=10)

    assignments = course.get_assignments()
    for assign in assignments:
        name = assign["name"]
        # print(f"\tProcessing Assignment: {name}")

        assigned = assign["assigned"]
        due = assign["due"]

        if assigned is None and due is None:
            continue

        base_name = f"{name} - {shortname}"
        if assigned is not None:
            event = Event()
            event.name = f"{base_name} Assigned"
            event.begin = assigned
            event.duration = event_size
            cal.events.add(event)

        if due is not None:
            event = Event()
            event.name = f"{base_name} Due"
            event.begin = due - event_size
            event.end = due
            cal.events.add(event)


with open("calendar.ics", "w") as f:
    f.writelines(cal.serialize_iter())
