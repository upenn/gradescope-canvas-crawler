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

import threading

def process_canvas_course(canvas_url, canvas_key, canvas_course_id):
    canvas = CanvasStatus(canvas_url, canvas_key, [canvas_course_id], config['canvas']['include'], config['canvas']['active_only'])

    canvas_courses, all_students, all_assignments, all_submissions, all_student_summaries = canvas.get_course_info()
    return (canvas_courses, all_students, all_assignments, all_submissions, all_student_summaries)

def process_gs_course(email, pwd, course):
    gs_students, gs_assignments, gs_submissions, gs_extensions = gs.get_course_info([course])
    return (gs_students, gs_assignments, gs_submissions, gs_extensions)


from gscdash.pycanvas.canvas_status import CanvasStatus
from gscdash.pyscope.gs_status import GradescopeStatus
import yaml
import pandas as pd


if __name__ == "__main__":
    with open('config.yaml') as config_file:
        config = yaml.safe_load(config_file)

        canvas_url = config['canvas']['site']
        canvas_key = config['canvas']['api_key']

        email = config['gradescope']["gs_login"]
        pwd = config['gradescope']['gs_pwd']
        use_threads = config['gradescope']['use_threads']

        print ('*** Reading details from config.yaml ***')

        if config['canvas']['enabled']:
            print ('Canvas courses:')
            all_students = []
            all_assignments = []
            all_submissions = []
            all_student_summaries = []
            for course_id in config['canvas']['course_ids']:
                print(course_id)

                canvas_courses, students, assignments, submissions, student_summaries = \
                    process_canvas_course(canvas_url, canvas_key, course_id)
                all_students.extend(students)
                all_assignments.extend(assignments)
                all_submissions.extend(submissions)
                all_student_summaries.extend(student_summaries)

            canvas_courses.to_csv('canvas_courses.csv',index=False)
            if len(all_student_summaries):
                pd.concat(all_student_summaries).to_csv('canvas_student_summaries.csv', index=False)
            if len(all_students):
                pd.concat(all_students).to_csv('canvas_students.csv', index=False)
            if len(all_assignments):
                pd.concat(all_assignments).to_csv('canvas_assignments.csv', index=False)
            if len(all_submissions):
                pd.concat(all_submissions).to_csv('canvas_submissions.csv', index=False)

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
            for course in courses:
                print(course.name)
                students, assignments, submissions, extensions = process_gs_course(email, pwd, course)
                gs_students.extend(students)
                gs_assignments.extend(assignments)
                gs_submissions.extend(submissions)
                gs_extensions.extend(extensions)

            pd.DataFrame(gs_courses).to_csv('gs_courses.csv',index=False)
            if len(gs_students):
                pd.concat(gs_students).to_csv('gs_students.csv', index=False)
            if len(gs_assignments):
                pd.concat(gs_assignments).to_csv('gs_assignments.csv', index=False)
            if len(gs_submissions):
                pd.concat(gs_submissions).to_csv('gs_submissions.csv', index=False)
            if len(gs_extensions):
                pd.concat(gs_extensions).to_csv('gs_extensions.csv', index=False)

