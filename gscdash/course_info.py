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

from abc import ABCMeta, abstractmethod
from typing import List, Tuple, Any
from datetime import datetime

import pandas as pd

class CourseDetails:
    course_uuid: str
    name: str
    starts: datetime
    ends: datetime

    def __str__(self, key):
        return '{}, {}, {}, {}'.format(self.course_uuid, self.name, self.starts, self.ends)
    
    def __iter__(self):
        yield self.course_uuid
        yield self.name
        yield self.starts
        yield self.ends 

class Assignment:
    assignment_uuid: str
    name: str
    due: datetime
    late: datetime
    points: int
    ec_points: int
    weight: float

class Person:
    data_id: str
    student_id: str
    name: str
    emails: List[str]
    user_id: str
    role: str

    def __str__(self, key):
        return '{}, {}, {}, {}, {}, {}'.format(self.data_id, self.student_id, self.name, self.emails, self.user_id, self.role)
    
    def __iter__(self):
        yield self.data_id
        yield self.student_id
        yield self.name
        yield self.emails
        yield self.user_id
        yield self.role

class CourseApi:
    @abstractmethod
    def get_course_list(self) -> List[CourseDetails]:
         raise NotImplementedError()
    
    def get_course_list_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.get_course_list())

    @abstractmethod    
    def get_assignments(self, course) -> List[Assignment]:
         raise NotImplementedError()
    
    def get_assignments_df(self, course) -> pd.DataFrame:
        return pd.DataFrame(self.get_assignments(course))

    @abstractmethod
    def get_quizzes(self, course) -> List[Assignment]:
        pass

    def get_quizzes_df(self, course) -> pd.DataFrame:
        return self.get_quizzes(course)

    @abstractmethod
    def get_students(self, course) -> List[Person]:
        raise NotImplementedError()
 
    def get_students_df(self, course) -> pd.DataFrame:
        return pd.DataFrame(self.get_students(course))
    
    @abstractmethod
    def get_assignment_submissions(self, course) -> List[Assignment]:
        raise NotImplementedError()
    
    def get_assignment_submissions_df(self, course) -> pd.DataFrame:
        return pd.DataFrame(self.get_assignment_submissions(course))

 
    # @abstractmethod
    # def get_instructors(self, course) -> List[Person]:
    #     raise NotImplementedError()

    # def get_instructors_df(self) -> pd.DataFrame:
    #     return pd.DataFrame(self.get_instructors())

class CourseWrapper(object):
    @abstractmethod
    def get_course_info(self) -> Tuple[Any]:
        """ 
        Fetch a tuple of lists of dataframes for each course, including students, assignments, submissions.
        """
        raise NotImplementedError()

