#####################################################################################################################
##
## Copyright (C) 2022-23 by Zachary G. Ives
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
#####################################################################################################################

from gscdash.pyscope import pyscope as gs
from gscdash.pyscope.pyscope import GSConnection
from gscdash.pyscope.pyscope import GSAccount, GSCourse
from gscdash.course_info import CourseWrapper
import pandas as pd
from datetime import datetime
import pytz
import logging

from typing import Tuple, Any, List, Callable

class GradescopeStatus(CourseWrapper):
    def __init__(self, email: str, pwd: str, semesters: list):
        conn = gs.GSConnection()

        print("Logging into Gradescope as %s..."%email)
        if not conn.login(email, pwd, semesters):
            print ('Error: Failed to log in!')
            return None

        self.sem = semesters
        # Get Account
        success = conn.get_account(semesters)
        if not success:
            print("Error: Failed to get account!")
            return None

        self.gs = conn
        self.account = conn.account

    def get_courses(self) -> List[GSCourse]:
        """
        Returns a list of all courses for an individual -- both as a student and instructor
        """
        return list(self.account.student_courses.values()) + \
            list(self.account.instructor_courses.values())


    def get_semesters(self, courses: List[GSCourse]) -> list:
        semesters = set()
        for course in courses:
            semesters.add(course.year)
        return list(semesters)

    def get_course_events(self, course: GSCourse, all_events: list, event_handler: Callable[[GSCourse, dict], None]):
        course_name = course.shortname
        print(f"\nStarted Processing Course: {course_name}")

        assignments = course.get_assignments()
        # all_events = []

        for assign in assignments:
            print(assign['name'], 'is due', assign['due'])
            events = event_handler(course, assign)
            all_events.extend(events)

        print(f"Finished Processing Course: {course_name}")

        return


    def fetch_gradescope_events(self, event_handler: Callable[[GSCourse, dict], None], use_threads):
        courses = self.get_courses()

        # cal = Calendar()
        # threads = []
        events = []
        students = []

        # if use_threads:
        #     for course in courses:
        #         if self.sem is not None:
        #             if course.year != self.sem:
        #                 continue

        #         thread = Thread(target=get_course_events, args=(course, events))
        #         thread.start()
        #         threads.append(thread)

        #     for thread in threads:
        #         thread.join()

        #     for event in events:
        #         cal.events.add(event)
        # else:
        for course in courses:
            if self.sem is not None:
                if course.year != self.sem:
                    continue

            print('Processing course %s...'%course.name);
            
            self.get_course_events(course, events, event_handler)
            # for event in events:
            #     cal.events.add(event)

            print('Getting course roster')
            for row in course.get_roster():
                print(row)
                students.add(row)

        # return cal.serialize_iter()
        return events, students


        
    def get_course_info(self) -> Tuple[Any]:
        gs_courses = self.gs.get_course_list_df()
        all_assignments = []
        all_students = []
        all_submissions = []
        all_student_summaries = []

        logging.debug('Getting course info from Gradescope for {}'.format(self.sem))

        rightnow = datetime.utcnow().replace(tzinfo=pytz.utc)
        for the_course in self.gs.get_course_list():
            print (the_course.name)

            students = self.gs.get_students_df(the_course)
            if len(students):
                students['course_id'] = the_course.cid
                print ('\nStudents:')
                print (students)
                all_students.append(students)

            assignments = self.gs.get_assignments_df(the_course)
            if len(assignments):
                assignments['course_id'] = the_course.cid
                print ('\nAssignments:')
                print(assignments)
                all_assignments.append(assignments)

            assignments = self.gs.get_assignment_submissions_df(the_course)
            if len(assignments):
                assignments['course_id'] = the_course.cid
                print ('\nAssignment submissions:')
                print(assignments)
                all_submissions.append(assignments)

            extensions = self.gs.get_extensions_df(the_course)
            if len(extensions):
                print(extensions)
                all_student_summaries.append(extensions)

        return ( gs_courses,
                all_students,
                all_assignments,
                all_submissions,
                all_student_summaries)