import requests
from bs4 import BeautifulSoup
from enum import Enum
from io import StringIO
from typing import List, Dict, Any
import logging
import pandas as pd
import lxml
import json
from gscdash.pyscope.account import GSAccount
from gscdash.pyscope.course import GSCourse

from python_canvas_layer.course_info import CourseApi

class ConnState(Enum):
    INIT = 0
    LOGGED_IN = 1


class GSConnection(CourseApi):
    """The main connection class that keeps state about the current connection."""

    def __init__(self):
        """Initialize the session for the connection."""
        self.session = requests.Session()
        self.state = ConnState.INIT
        self.account = None
        self.crawl_student = None

    def login(self, email, pswd, semesters):
        """
        Login to gradescope using email and password.
        Note that the future commands depend on account privilages.
        """
        init_resp = self.session.get("https://www.gradescope.com/")
        parsed_init_resp = BeautifulSoup(init_resp.text, "html.parser")
        for form in parsed_init_resp.find_all("form"):
            if form.get("action") == "/login":
                for inp in form.find_all("input"):
                    if inp.get("name") == "authenticity_token":
                        auth_token = inp.get("value")

        login_data = {
            "utf8": "✓",
            "session[email]": email,
            "session[password]": pswd,
            "session[remember_me]": 0,
            "commit": "Log In",
            "session[remember_me_sso]": 0,
            "authenticity_token": auth_token,
        }
        login_resp = self.session.post("https://www.gradescope.com/login", params=login_data)
        if len(login_resp.history) != 0:
            if login_resp.history[0].status_code == requests.codes.found:
                self.state = ConnState.LOGGED_IN
                self.account = GSAccount(email, self.session)
                self.get_account(semesters)
                return True
        else:
            return False

    def get_account(self, semesters):
        """
        Gets and parses account data after login. Note will return false if we are not in a logged in state, but
        this is subject to change.
        """
        if self.state != ConnState.LOGGED_IN:
            raise "No login"
            return False  # Should raise exception
        # Get account page and parse it using bs4
        account_resp = self.session.get("https://www.gradescope.com/account")
        parsed_account_resp = BeautifulSoup(account_resp.text, "html.parser")

        # Get instructor course data. This is called "Your Courses" if there is only
        # one type of course, or "Instructor Courses" if not
        instructor_courses = parsed_account_resp.find("h1", class_="pageHeading").next_sibling#.next_sibling

        if not instructor_courses.find_all("a", class_="courseBox"):
            instructor_courses = instructor_courses.next_sibling

        if not instructor_courses or len(instructor_courses) == 0:
            print ('No instructor courses found')

        for course in instructor_courses.find_all("a", class_="courseBox"):
            logging.debug ('Found course box')
            shortname = course.find("h3", class_="courseBox--shortname").text
            name = course.find("div", class_="courseBox--name").text
            cid = course.get("href").split("/")[-1]
            year = None
            # print ('Instructor role in: ', cid, name, shortname)
            for tag in course.parent.previous_siblings:
                if "courseList--term" in tag.get("class"):
                    year = tag.string
                    break
            if year is None:
                raise "No year"
                return False  # Should probably raise an exception.
            
            if semesters is None or year in semesters:
                # print(year)
                new_course = self.account.add_class(
                    cid, name, shortname, year, instructor=False
                )
                new_course.get_lti_link()

        if self.crawl_student:
            student_courses = parsed_account_resp.find(
                "h1", class_="pageHeading", string="Student Courses"
            )

            if student_courses is None:
                print('No student courses found')
                return True

            student_courses = student_courses.next_sibling

            year = None
            for course in student_courses.find_all("a", class_="courseBox"):
                shortname = course.find("h3", class_="courseBox--shortname").text
                name = course.find("div", class_="courseBox--name").text
                cid = course.get("href").split("/")[-1]
                # print('Student in: ', cid, name, shortname)

                for tag in course.parent.previous_siblings:
                    if tag.get("class") == "courseList--term pageSubheading":
                        year = tag.body
                        break
                if year is None:
                    raise "No year"
                    return False  # Should probably raise an exception.
                if semesters is None or year in semesters:
                    # print(year)
                    new_course = self.account.add_class(cid, name, shortname, year)

        return True

    def get_course_list(self) -> List[Dict]:
        icourses = []
        scourses = []
        if self.account.instructor_courses and len(self.account.instructor_courses):
            icourses = list(self.account.instructor_courses.values())
        if self.account.student_courses and len(self.account.student_courses):
            scourses = list(self.account.student_courses.values())

        return icourses + scourses
    
    def get_course_list_df(self) -> pd.DataFrame:
        ret = pd.DataFrame([vars(item) for item in self.get_course_list()])
        
        if len(ret):
            return ret.drop(columns=['session','roster','assignments','state'])
        else:
            return ret

    def get_course(self, cid) -> GSCourse:
        return self.get_course(cid)
    
    def get_assignments(self, course: GSCourse) -> List[Dict]:
        return course.get_assignments()
    
    # def get_assignments_df(self, course: GSCourse) -> pd.DataFrame:
    #     return super().get_assignments_df(course)
    

    def get_students(self, course: GSCourse) -> List[Dict]:
        return list(course.get_roster().values())
    
    def get_students_df(self, course: GSCourse) -> pd.DataFrame:
        ret = pd.DataFrame(self.get_students(course))
        if len(ret):
            ret.columns = ['sid', 'student_id', 'name', 'emails', 'user_id', 'role']
        return ret

    def get_assignment_submissions_df(self, course: GSCourse) -> pd.DataFrame:
        assignments = []
        for assignment in course.get_assignments():
            if 'id' in assignment:
                scores = self.session.get('https://gradescope.com/courses/' + course.cid + '/assignments/' + assignment['id'] + '/scores.csv').text

                # print(scores)

                assignments.append(pd.read_csv(StringIO(scores)))
                assignments[-1]['course_id'] = course.cid
                assignments[-1]['assign_id'] = assignment['id']

        if len(assignments):
            return pd.concat(assignments)
        else:
            return pd.DataFrame([{}])
    
    def get_assignment_submissions(self, course: GSCourse) -> List[Dict]:
         return self.get_assignment_submissions_df.to_list()
    
    def get_extensions_df_list(self, course: GSCourse) -> List[pd.DataFrame]:
        extensions = []
        for assignment in course.get_assignments():
            if 'id' in assignment:
                ext_table = self.session.get('https://gradescope.com/courses/' + course.cid + '/assignments/' + assignment['id'] + '/extensions').text

                # print("{}".format(ext_table))
                try:
                    tab_list = pd.read_html(StringIO(ext_table))

                    # print (tab_list)

                    extensions.append(tab_list[0].copy())
                    extensions[-1]['course_id'] = course.cid
                    extensions[-1]['assign_id'] = assignment['id']

                    parsed_ext_resp = BeautifulSoup(ext_table, 'html.parser')
                    tbody_element = parsed_ext_resp.find('tbody')

                    tr_elements = tbody_element.find_all('tr')
                    new_list = []
                    for row in tr_elements:
                        td_elements = row.find_all('td')
                        user_name = td_elements[0].text

                        div = row.find('div', attrs = {'data-react-class': 'EditExtension'})
                        if div:
                            props = div['data-react-props'].replace('&quot;', '"')
                            props_json = json.loads(props)
                            new_list.append({'user_id': int(props_json['userId'])})#, 'user_name': user_name})
                            print ('Extension for user {}: {}'.format(user_name, props_json['userId']))

                    extensions[-1] = extensions[-1].merge(pd.DataFrame(new_list), left_index=True, right_index=True)
                except ValueError:
                    pass
        return extensions
    
    def get_extensions_df(self, course: GSCourse) -> pd.DataFrame:
        results = self.get_extensions_df_list(course)
        if len(results):
            return pd.concat(results)
        else:
            return pd.DataFrame([{}])
    
    def get_extensions(self, course: GSCourse) -> List[Dict]:
        return self.get_extensions_df(course).to_list()
