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

from gscdash.pycanvas.pycanvas import CanvasConnection
from gscdash.course_info import CourseWrapper
import pandas as pd
from datetime import datetime
import pytz
import logging

from typing import Tuple, Any, List

class CanvasStatus(CourseWrapper):
    def __init__(self, canvas_url, canvas_key, filter_course_ids: List[str], options: List[str], active: bool):
        self.canvas = CanvasConnection(canvas_url, canvas_key)
        self.course_id_list = filter_course_ids
        self.options = options
        self.active = active

        
    def get_course_info(self) -> Tuple[Any]:
        canvas_courses = self.canvas.get_course_list_df()
        all_assignments = []
        all_students = []
        all_submissions = []
        all_student_summaries = []

        logging.debug('Getting course info from Canvas for {}'.format(self.course_id_list))

        rightnow = datetime.utcnow().replace(tzinfo=pytz.utc)
        for the_course in self.canvas.get_course_list_objs():

            if self.course_id_list and len(self.course_id_list) and the_course.id not in self.course_id_list:
                continue
            else:
                print (the_course.name)

            # Ensure the course is currently being offered (ie active)
            if (True or (not self.active or (the_course.end_at and \
            (pd.to_datetime(the_course.start_at, utc=True) <= rightnow and rightnow <= pd.to_datetime(the_course.end_at, utc=True))))):

                logging.debug ('{} through {}'.format(the_course.start_at, the_course.end_at))

                # OPTIONAL but not really needed since Quizzes are also Assignments?
                if 'quizzes' in self.options:
                    quizzes = self.canvas.get_quizzes_df(the_course)
                    if len(quizzes):
                        quizzes['course_id'] = the_course.id
                        print ('\nQuizzes:')
                        print(quizzes)

                # OPTIONAL: do we want modules and module items?
                if 'modules' in self.options:
                    modules = self.canvas.get_modules_df(the_course)
                    if len(modules):
                        modules['course_id'] = the_course.id
                        print ('\nModules:')
                        print(modules)
                    module_items = self.canvas.get_module_items_df(the_course)
                    if len(module_items):
                        print ('\nItems in modules:')
                        print(module_items)

                if 'students' in self.options:
                    print ('\nRecording enrolled students')
                    students = self.canvas.get_students_df(the_course)
                    if len(students):
                        students['course_id'] = the_course.id
                        print (len(students))
                        all_students.append(students)

                if 'assignments' in self.options:
                    print ('\nRecording course assignments')
                    assignments = self.canvas.get_assignments_df(the_course)
                    if len(assignments):
                        assignments['course_id'] = the_course.id
                        print(len(assignments))
                        all_assignments.append(assignments)

                # Get general student status, including late days etc
                if 'summaries' in self.options:
                    print ('\nRecording student summaries')
                    student_summaries = self.canvas.get_student_summaries_df(the_course)
                    if len(student_summaries):
                        print (len(student_summaries))
                        all_student_summaries.append(student_summaries)

                if 'submissions' in self.options:
                    print ('\nRecording assignment submissions')
                    assignments = self.canvas.get_assignment_submissions_df(the_course)
                    if len(assignments):
                        assignments['course_id'] = the_course.id
                        print(len(assignments))
                        all_submissions.append(assignments)

        return ( canvas_courses,
                all_students,
                all_assignments,
                all_submissions,
                all_student_summaries)