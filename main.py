from threading import Thread
from pyscope import pyscope as gs
from ics import Calendar, Event
import datetime
from getpass import getpass
import os

from pyscope.account import GSAccount, GSCourse


def login(email, pwd) -> GSAccount:
    conn = gs.GSConnection()

    print("Logging in...")
    conn.login(email, pwd)

    # Get Account
    success = conn.get_account()
    if not success:
        print("Failed to get account")
        return None

    return conn.account


def get_courses(acct: GSAccount) -> list[GSCourse]:
    return list(acct.student_courses.values())


def get_semesters(courses: list[GSCourse]) -> list[str]:
    semesters = set()
    for course in courses:
        semesters.add(course.year)
    return list(semesters)


def create_hw_events(course: GSCourse, assignment: dict) -> list[Event]:
    name = assignment["name"]
    # print(f"\tProcessing Assignment: {name}")

    assigned = assignment["assigned"]
    due = assignment["due"]

    date_printfmt = "%A, %d. %B %Y %I:%M%p"

    desc = f"""Course: {course.name}
Course Shortname: {course.shortname}
Link to Course: {course.get_url()}

Assignment: {name}
Assigned: {assigned.strftime(date_printfmt) if assigned is not None else "None"}
Due: {due.strftime(date_printfmt) if due is not None else "None"}"""

    out = []

    def hw_event(name, course_name, type, time):
        event = Event()
        event.name = f"{name} - {course_name} {type}"
        event.begin = time
        event.end = time
        event.description = desc
        return event

    if assigned is not None:
        out.append(hw_event(name, course.shortname, "Assigned", assigned))

    if due is not None:
        out.append(hw_event(name, course.shortname, "Due", due))

    return out


def get_course_events(course: GSCourse, all_events: list[Event]):
    course_name = course.shortname
    print(f"Started Processing Course: {course_name}")

    assignments = course.get_assignments()
    # all_events = []

    for assign in assignments:
        events = create_hw_events(course, assign)
        all_events.extend(events)

    print(f"Finished Processing Course: {course_name}")

    return


def do_the_thing(email, pwd, sem=None):
    acct: GSAccount = login(email, pwd)
    courses = get_courses(acct)

    cal = Calendar()
    threads = []
    events = []

    for course in courses:
        if sem is not None:
            if course.year != sem:
                continue

        thread = Thread(target=get_course_events, args=(course, events))
        thread.start()
        threads.append(thread)
        # events = get_course_events(course)
        # for event in events:
        #     cal.events.add(event)

    for thread in threads:
        thread.join()

    for event in events:
        cal.events.add(event)

    return cal.serialize_iter()


if __name__ == "__main__":
    email = os.environ.get("GS_EMAIL")
    pwd = os.environ.get("GS_PWD")
    sem = os.environ.get("GS_SEM")

    # Login
    if email is None:
        email = input("Email: ")
    if pwd is None:
        pwd = getpass("Password: ")
    if sem is None:
        sem = input("Semester: ")

    with open("gradescope.ics", "w") as f:
        f.writelines(do_the_thing(email, pwd, sem))
