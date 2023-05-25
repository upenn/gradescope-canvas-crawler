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

from canvasapi import Canvas
from canvasapi.course import Course
from canvasapi.module import Module
from canvasapi.assignment import Assignment
from canvasapi.exceptions import *
from canvasapi.paginated_list import PaginatedList
import pandas as pd
from gscdash.course_info import CourseApi
import logging
from typing import List, Dict

class CanvasConnection(CourseApi):
    def __init__(self, canvas_url, canvas_key):
        self.canvas = Canvas(canvas_url, canvas_key)

        self.get_course_list_full()
        return
    
    def _get_paginated(the_list, paginated: PaginatedList):
        for item in paginated:
            the_list.append(item)

        return the_list
    
    def get_course_list(self) -> List[Dict]:
        return self.courses

    def get_course_list_objs(self) -> List[Course]:
        return self.course_objs
    
    def get_course_list_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.get_course_list())
    
    def get_course_list_full(self) -> pd.DataFrame:
        course_list = []
        CanvasConnection._get_paginated(course_list, self.canvas.get_courses(per_page=100))
        self.courses = []
        self.course_objs = []
        for course in course_list:
            self.course_objs.append(course)
            self.courses.append({
                'id': course.id,
                'name': course.name,
                'start_at': course.start_at,
                'end_at': course.end_at,
                'workflow_state': course.workflow_state,
                'course_code': course.course_code,
                # 'sis_course_id': course.sis_course_id,
                # 'integration_id': course.integration_id,
                # 'hide_final_grades': course.hide_final_grades,
                'is_public': course.is_public,
           })
            
        return self.courses
    
    def get_course(self, course_id: str) -> Course:
        return self.canvas.get_course(course_id)

    def get_quizzes(self, course: Course) -> List[Dict]:
        """
        Returns a list of dictionaries containing the quizzes for a course.
        """
        quizzes = []
        try:
            quiz_list = []
            CanvasConnection._get_paginated(quiz_list, course.get_quizzes(per_page=100))
            for quiz in quiz_list:
                quizzes.append({'id':quiz.id,'title':quiz.title,'published':quiz.published,\
                    'unlock_at': quiz.unlock_at, 'due_at': quiz.due_at, 'lock_at': quiz.lock_at, 'published': quiz.published})
        except ResourceDoesNotExist:
            logging.warning('No quizzes found for course %s', course)
            pass

        return quizzes
    
    def get_quizzes_df(self, course: Course) -> pd.DataFrame:
        return pd.DataFrame(self.get_quizzes(course))

    def get_modules(self, course: Course) -> List[Dict]:
        """
        Returns a list of dictionaries containing the modules for a course.
        """
        modules = []
        mods = []
        CanvasConnection._get_paginated(mods, course.get_modules(per_page=100))
        for module in mods:
            try:
                modules.append({
                    'id': module.id,
                    'name': module.name,
                    'published': module.published,
                    'unlock_at': module.unlock_at
                })
            except AttributeError:
                modules.append({
                    'id': module.id,
                    'name': module.name,
                    'unlock_at': module.unlock_at
                })

        return modules
    
    def get_modules_df(self, course: Course) -> pd.DataFrame:
        return pd.DataFrame(self.get_modules(course))

    def get_module_items(self, course: Course) -> List[Dict]:
        """
        Returns a list of dictionaries containing the module items for a course.
        """
        module_items = []
        mods = []
        CanvasConnection._get_paginated(mods, course.get_modules(per_page=100))
        for module in mods:
            mod_items = []
            CanvasConnection._get_paginated(mod_items, module.get_module_items(per_page=100))
            for item in mod_items:
                try:
                    details = {
                        'module_id': module.id,
                        'module_name': module.name,
                        'id': item.id,
                        'title': item.title,
                        # 'published': item.published,
                        'type': item.type,
                        'html_url': item.html_url
                    }
                except AttributeError:
                    details = {
                        'module_id': module.id,
                        'module_name': module.name,
                        'id': item.id,
                        'title': item.title,
                        # 'published': item.published,
                        'type': item.type
                    }

                if item.type == 'Quiz':
                    details['url'] = item.url
                if item.type == 'ExternalUrl':
                    details['external_url'] = item.external_url

                try:
                    details['published'] = item['published']
                except:
                    pass
                module_items.append(details)
        return module_items

    def get_module_items_df(self, course: Course) -> pd.DataFrame:
        return pd.DataFrame(self.get_module_items(course))

    def get_matching_module_url(self, module_items: List[Module], index: str, typ: str) -> str:
        matches = module_items[module_items['title'].apply(lambda x: x.startswith(index))]
        if len(matches):
            matches = matches[matches['type'] == typ]
        if len(matches):
            if typ == 'Quiz':
                return matches['html_url'].array[0]
            else:
                return matches['external_url'].array[0]
            
    def get_assignments(self, course: Course) -> List[Dict]:
        """
        Returns a list of dictionaries containing the assignments for a course.
        """
        assignments = []
        ret = []
        CanvasConnection._get_paginated(assignments, course.get_assignments(per_page=100))
        for assignment in assignments:
            ret.append(vars(assignment))
            del(ret[-1]['_requester'])
            del(ret[-1]['description'])
            del(ret[-1]['secure_params'])
        return ret
            
    def get_student_summaries_df(self, course: Course) -> pd.DataFrame:
        """
        Returns a dataframe containing the student summaries for a course.
        """
        try:
            the_list = []
            summaries = []
            CanvasConnection._get_paginated(the_list, course.get_course_level_student_summary_data(per_page=100))
            for item in the_list:
                summaries.append(vars(item))
                del(summaries[-1]['_requester'])
            ret = pd.DataFrame(summaries)
            if 'tardiness_breakdown' in ret.columns:
                return ret.join(pd.json_normalize(ret['tardiness_breakdown'])).drop(['tardiness_breakdown'], axis=1)
            else:
                return ret
        except Forbidden:
            return pd.DataFrame()
        except ResourceDoesNotExist:
            return pd.DataFrame()

            

    def get_students(self, course) -> List[Dict]:
        students = []
        ret= []
        try:
            CanvasConnection._get_paginated(students, course.get_users(enrollment_type=['student'], per_page=100))
            for student in students:
                ret.append(vars(student))
                del(ret[-1]['_requester'])
        except ResourceDoesNotExist:
            logging.warning('No students found for course %s', course)
            pass
        except Forbidden:
            logging.warning('Unauthorized to access students for course %s', course)
            pass
    
        return ret
    
    def get_assignment_submissions(self, course: Course) -> List[Dict]:
        """
        Returns a list of dictionaries containing the assignment submissions for a course.
        """
        ret = []
        assignments = []
        CanvasConnection._get_paginated(assignments, course.get_assignments(per_page=100))
        try:
            for assignment in assignments:
                submissions = []
                CanvasConnection._get_paginated(submissions, assignment.get_submissions(per_page=100))
                for submission in submissions:
                    ret.append(vars(submission))
                    ret[-1]['assignment_id'] = assignment.id
                    del(ret[-1]['_requester'])
        except ResourceDoesNotExist:
            pass
        except Forbidden:
            pass
        return ret
    
    def get_assignment_submissions_df(self, course: Course) -> pd.DataFrame:
        return pd.DataFrame(self.get_assignment_submissions(course))