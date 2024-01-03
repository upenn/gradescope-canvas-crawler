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
## Modifications by Zack Ives, 2023+.
##
## Forms the crawler component for a broader Penn CIS Teaching Dashboard, https://github.com/upenn/gradescope-canvas-dashboard.
## The dashboard component is licensed under the Apache 2.0 license.
##
## Usage:
##  * Update config.yaml (copied from config.yaml.default) to include a Gradescope user ID and password.
##  * In Canvas, go to Settings, User Settings and add a New Access Token.  Copy the API key into config.yaml
##  * Copy the course IDs of any Canvas courses you'd like to add
##
#####################################################################################################################

import os
import pandas as pd
from database import config, dbEngine

from gscdash.pycanvas.canvas_status import CanvasStatus
from gscdash.pyscope.gs_status import GradescopeStatus

def process_canvas_course(canvas_url, canvas_key, canvas_course_id):
    canvas = CanvasStatus(canvas_url, canvas_key, [canvas_course_id], config['canvas']['include'], config['canvas']['active_only'])

    canvas_courses, all_students, all_assignments, all_submissions, all_student_summaries = canvas.get_course_info()
    return (canvas_courses, all_students, all_assignments, all_submissions, all_student_summaries)

def process_gs_course(email, pwd, course):
    gs_students, gs_assignments, gs_submissions, gs_extensions = gs.get_course_info([course])
    return (gs_students, gs_assignments, gs_submissions, gs_extensions)

def write(dataframe: pd.DataFrame, name: str, first: bool = True):
    if first:
        dataframe.to_sql(name, dbEngine, if_exists='replace', index=False)
    else:
        dataframe.to_sql(name, dbEngine, if_exists='append', index=False)

if __name__ == "__main__":
    canvas_url = config['canvas']['site']
    canvas_key = config['canvas']['api_key']

    email = config['gradescope']["gs_login"]
    pwd = config['gradescope']['gs_pwd']
    use_threads = config['gradescope']['use_threads']

    print ('*** Reading details from config.yaml ***')

    os.makedirs('./data', exist_ok=True) 

    if config['canvas']['enabled']:
        print ('Canvas courses:')
        all_students = []
        all_assignments = []
        all_submissions = []
        all_student_summaries = []
        first = True
        for course_id in config['canvas']['course_ids']:
            print(course_id)

            canvas_courses, students, assignments, submissions, student_summaries = \
                process_canvas_course(canvas_url, canvas_key, course_id)
            all_students.extend(students)
            all_assignments.extend(assignments)
            all_submissions.extend(submissions)
            all_student_summaries.extend(student_summaries)
            write(pd.concat(student_summaries), 'canvas_student_summaries', first)
            write(pd.concat(students), 'canvas_students', first)
            write(pd.concat(assignments), 'canvas_assignments', first)
            write(pd.concat(submissions), 'canvas_submissions', first)

            first = False

        canvas_courses.to_csv('data/canvas_courses.csv',index=False)
        write(canvas_courses, 'canvas_courses', True)
        if len(all_student_summaries):
            pd.concat(all_student_summaries).to_csv('data/canvas_student_summaries.csv', index=False)

        if len(all_students):
            pd.concat(all_students).to_csv('data/canvas_students.csv', index=False)

        if len(all_assignments):
            pd.concat(all_assignments).to_csv('data/canvas_assignments.csv', index=False)

        if len(all_submissions):
            pd.concat(all_submissions).to_csv('data/canvas_submissions.csv', index=False)

    if config['gradescope']['enabled']:
        print ('Gradescope semesters')
        if 'semesters' in config['gradescope']:
            for sem in config['gradescope']['semesters']:
                print(sem)
        else:
            print ("all")

        gs = GradescopeStatus(email, pwd, config['gradescope']['semesters'])
        courses = gs.gs.get_course_list()

        gs_courses = gs.gs.get_course_list_df()
        gs_students = []
        gs_assignments = []
        gs_submissions = []
        gs_extensions = []
        first = True
        for course in courses:
            print(course.name)
            students, assignments, submissions, extensions = process_gs_course(email, pwd, course)
            gs_students.extend(students)
            gs_assignments.extend(assignments)
            gs_submissions.extend(submissions)
            gs_extensions.extend(extensions)

            student_tbl = pd.concat(students).explode('emails')
            student_tbl['role'] = student_tbl['role'].apply(lambda x: x.name)
            student_tbl['user_id'] = student_tbl['user_id'].apply(lambda x: x if x != '' else None)
            student_tbl['student_id'] = student_tbl['student_id'].apply(lambda x: x if x != '' else None)
            student_tbl = student_tbl.astype({'sid': str, 'course_id': int})
            write(student_tbl, 'gs_students', first)
            assignment_tbl = pd.concat(assignments).astype({'id': int, 'course_id': int})
            write(assignment_tbl, 'gs_assignments', first)
            submission_tbl = pd.concat(submissions).astype({'SID': str, 'course_id': int, 'assign_id': int})
            submission_tbl = submission_tbl[['First Name', 'Last Name', 'SID', 'Email','course_id','assign_id', 'Sections', 'Total Score', 'Max Points', 'Status', 'Submission ID', 'Submission Time', 'Lateness (H:M:S)', 'View Count', 'Submission Count']]
            write(submission_tbl, 'gs_submissions', first)
            extension_tbl = pd.concat(extensions).astype({'course_id': int, 'assign_id': int, 'user_id': int})
            write(extension_tbl, 'gs_extensions', first)

            first = False

        gs_courses = gs_courses.astype({'cid': int, 'lti': int})
        gs_courses.to_csv('data/gs_courses.csv',index=False)
        write(gs_courses, 'gs_courses', True)
        if len(gs_students):
            pd.concat(gs_students).to_csv('data/gs_students.csv', index=False)

        if len(gs_assignments):
            pd.concat(gs_assignments).to_csv('data/gs_assignments.csv', index=False)

        if len(gs_submissions):
            pd.concat(gs_submissions).to_csv('data/gs_submissions.csv', index=False)

        if len(gs_extensions):
            pd.concat(gs_extensions).to_csv('data/gs_extensions.csv', index=False)

