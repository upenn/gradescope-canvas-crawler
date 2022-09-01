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
    course_name = course.shortname
    print(f"Processing Course: {course_name}")

    assignments = course.get_assignments()
    for assign in assignments:
        name = assign["name"]
        # print(f"\tProcessing Assignment: {name}")

        assigned = assign["assigned"]
        due = assign["due"]

        date_printfmt = "%A, %d. %B %Y %I:%M%p"

        desc = f"""Course: {course.name}
Course Shortname: {course.shortname}

Assignment: {name}
Assigned: {assigned.strftime(date_printfmt) if assigned is not None else "None"}
Due: {due.strftime(date_printfmt) if due is not None else "None"}"""

        if assigned is None and due is None:
            continue

        def hw_event(name, type, time):
            global course_name

            event = Event()
            event.name = f"{name} - {course_name} {type}"
            event.begin = time
            event.end = time
            event.description = desc
            return event

        if assigned is not None:
            cal.events.add(hw_event(name, "Assigned", assigned))

        if due is not None:
            cal.events.add(hw_event(name, "Due", due))


with open("calendar.ics", "w") as f:
    f.writelines(cal.serialize_iter())
