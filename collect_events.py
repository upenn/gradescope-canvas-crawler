#####################################################################################################################
##
## Course Event Crawler
##
## 
## Gradescope components are derived from Sagar Reddy Patil's Gradescope iCalendar Converter, 
## https://github.com/sagarredypatil/gradescope-ics, which also leverages the original Gradescope codebase from 
## Anton Pozharski, https://github.com/apozharski/gradescope-api.
##
## All original license terms apply.
##
## Modifications by Zack Ives and are licensed under the Apache License 2.0
##
## Usage:
##  * Update config.yaml (copied from config.yaml.default) to include a Gradescope user ID and password.
##  * In Canvas, go to Settings, User Settings and add a New Access Token.  Copy the API key into config.yaml
##  * Copy the course IDs of any Canvas courses you'd like to add
##
#####################################################################################################################


from threading import Thread
from pyscope import pyscope as gs
from pycanvas.pycanvas import CanvasConnection
from ics import Calendar, Event
import datetime
import os
import hashlib
import yaml
import logging
import pandas as pd
import pytz

from pyscope.account import GSAccount, GSCourse

#from pycanvas.pycanvas import get_quizzes, get_modules, get_module_items


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


def fetch_gradescope_events(email:str, pwd:str, sem, use_threads):
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
        #      f.writelines(fetch_gradescope_events(email, pwd, sem, use_threads))

        canvas = CanvasConnection(canvas_url, canvas_key)
        items = 3

        canvas_courses = canvas.get_course_list_df()
        all_assignments = []
        all_students = []
        all_submissions = []
        all_student_summaries = []

        rightnow = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        for the_course in canvas.get_course_list_objs():#config['canvas']['course_ids']:
            print (the_course.name)

            if (the_course.end_at and \
            (pd.to_datetime(the_course.start_at, utc=True) <= rightnow and rightnow <= pd.to_datetime(the_course.end_at, utc=True))):

                print ('{} through {}'.format(the_course.start_at, the_course.end_at))
                # quizzes = canvas.get_quizzes_df(the_course)
                # if len(quizzes):
                #     quizzes['course_id'] = the_course.id
                #     print ('\nQuizzes:')
                #     print(quizzes)

                assignments = canvas.get_assignments_df(the_course)
                if len(assignments):
                    assignments['course_id'] = the_course.id
                    print ('\nAssignments:')
                    print(assignments)
                    all_assignments.append(assignments)

                # modules = canvas.get_modules_df(the_course)
                # if len(modules):
                #     modules['course_id'] = the_course.id
                #     print ('\nModules:')
                #     print(modules)
                # module_items = canvas.get_module_items_df(the_course)
                # if len(module_items):
                #     print ('\nItems in modules:')
                #     print(module_items)

                # Todo: Get student status
                student_summaries = canvas.get_student_summaries_df(the_course)
                if len(student_summaries):
                    print ('\nStudent summaries:')
                    print (student_summaries)
                    all_student_summaries.append(student_summaries)

                students = canvas.get_students_df(the_course)
                if len(students):
                    students['course_id'] = the_course.id
                    print ('\nStudents:')
                    print (students)
                    all_students.append(students)

                assignments = canvas.get_assignment_submissions_df(the_course)
                if len(assignments):
                    assignments['course_id'] = the_course.id
                    print ('\nAssignment submissions:')
                    print(assignments)
                    all_submissions.append(assignments)

                items -= 1
                if (items < 0):
                    break

        canvas_courses.to_csv('canvas_courses.csv',index=False)
        if len(all_student_summaries):
           pd.concat(all_student_summaries).to_csv('student_summaries.csv', index=False)
        if len(all_students):
            pd.concat(all_students).to_csv('students.csv', index=False)
        if len(all_assignments):
            pd.concat(all_assignments).to_csv('assignments.csv', index=False)
        if len(all_submissions):
            pd.concat(all_submissions).to_csv('submissions.csv', index=False)