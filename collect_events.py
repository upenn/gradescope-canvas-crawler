from threading import Thread
from pyscope import pyscope as gs
from ics import Calendar, Event
import datetime
import os
import hashlib
import yaml
from canvasapi import Canvas

from pyscope.account import GSAccount, GSCourse

from pycanvas.pycanvas import get_quizzes, get_modules, get_module_items


def login(email: str , pwd: str) -> GSAccount:
    conn = gs.GSConnection()

    print("Logging into Gradescope as %s..."%email)
    if not conn.login(email, pwd):
        print ('Error: Failed to log in!')
        return None

    # Get Account
    success = conn.get_account()
    if not success:
        print("Error: Failed to get account!")
        return None

    return conn.account


def get_courses(acct: GSAccount) -> list:
    return list(acct.student_courses.values()) + \
        list(acct.instructor_courses.values())


def get_semesters(courses: list) -> list:
    semesters = set()
    for course in courses:
        semesters.add(course.year)
    return list(semesters)


def create_hw_events(course: GSCourse, assignment: dict) -> list:
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

    def hw_event(name:str, course_name:str, type, time):
        event = Event()
        event.name = f"{name} - {course_name} {type}"
        event.begin = time
        event.end = time
        event.description = desc

        hash = f"{name}{course_name}{time.strftime('%Y%m%d')}"
        hash = hashlib.sha1(hash.encode("utf-8")).hexdigest()
        event.uid = f"{hash}@cis.upenn.edu"
        return event

    if assigned is not None:
        out.append(hw_event(name, course.shortname, "Assigned", assigned))

    if due is not None:
        out.append(hw_event(name, course.shortname, "Due", due))

    return out


def get_course_events(course: GSCourse, all_events: list):
    course_name = course.shortname
    print(f"\nStarted Processing Course: {course_name}")

    assignments = course.get_assignments()
    # all_events = []

    for assign in assignments:
        print(assign['name'], 'is due', assign['due'])
        events = create_hw_events(course, assign)
        all_events.extend(events)

    print(f"Finished Processing Course: {course_name}")

    return


def crawl(email:str, pwd:str, sem, use_threads):
    acct: GSAccount = login(email, pwd)
    courses = get_courses(acct)

    cal = Calendar()
    threads = []
    events = []

    if use_threads:
        for course in courses:
            if sem is not None:
                 if course.year != sem:
                     continue

            thread = Thread(target=get_course_events, args=(course, events))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        for event in events:
            cal.events.add(event)
    else:
        for course in courses:
            if sem is not None:
                 if course.year != sem:
                     continue

            print('Processing course %s...'%course.name);
            
            get_course_events(course, events)
            for event in events:
                cal.events.add(event)

            print('Getting course roster')
            for row in course.get_roster():
                print(row)

    return cal.serialize_iter()


if __name__ == "__main__":
    with open('config.yaml') as config_file:
        config = yaml.safe_load(config_file)

        canvas_url = config['canvas']['site']
        canvas_key = config['canvas']['api_key']

        email = config['gradescope']["gs_login"]
        pwd = config['gradescope']['gs_pwd']
        use_threads = config['gradescope']['use_threads']

        sem = None
        if sem in config:
            sem = config['semester']

        # with open("gradescope.ics", "w") as f:
        #     f.writelines(crawl(email, pwd, sem, use_threads))

        canvas = Canvas(canvas_url, canvas_key)
        for course in config['canvas']['course_ids']:
            the_course = canvas.get_course(course)

            quizzes = get_quizzes(the_course)
            modules = get_modules(the_course)
            module_items = get_module_items(the_course)

