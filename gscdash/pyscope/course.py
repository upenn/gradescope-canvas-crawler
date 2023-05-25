from enum import Enum
from bs4 import BeautifulSoup
from datetime import datetime
from gscdash.pyscope.person import GSPerson
from gscdash.pyscope.person import GSRole
from gscdash.pyscope.assignment import GSAssignment


class LoadedCapabilities(Enum):
    ASSIGNMENTS = 0
    ROSTER = 1


class GSCourse:
    def __init__(self, cid, name, shortname, year, session):
        """Create a course object that has lazy eval'd assignments"""
        self.cid = cid
        self.name = name
        self.shortname = shortname
        self.year = year
        self.session = session
        self.assignments = {}
        self.roster = {}  # TODO: Maybe shouldn't dict.
        self.state = (
            set()
        )  # Set of already loaded entities (TODO what is the pythonic way to do this?)

    # ~~~~~~~~~~~~~~~~~~~~~~PEOPLE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_url(self):
        return "https://www.gradescope.com/courses/" + self.cid
    
    def get_roster(self):
        self._check_capabilities({LoadedCapabilities.ROSTER})

        return self.roster

    def add_person(self, name, email, role, sid=None, notify=False):
        self._check_capabilities({LoadedCapabilities.ROSTER})

        membership_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/memberships"
        )
        parsed_membership_resp = BeautifulSoup(membership_resp.text, "html.parser")

        authenticity_token = parsed_membership_resp.find("meta", attrs={"name": "csrf-token"}).get(
            "content"
        )
        person_params = {
            "utf8": "✓",
            "user[name]": name,
            "user[email]": email,
            "user[sid]": "" if sid is None else sid,
            "course_membership[role]": role.value,
            "button": "",
        }
        if notify:
            person_params["notify_by_email"] = 1
        # Seriously. Why is this website so inconsistent as to where the csrf token goes?????????
        add_resp = self.session.post(
            "https://www.gradescope.com/courses/" + self.cid + "/memberships",
            data=person_params,
            headers={"x-csrf-token": authenticity_token},
        )

        # TODO this is highly wasteful, need to likely improve this.
        self.roster = {}
        self._lazy_load_roster()

    def remove_person(self, name):
        self._check_capabilities({LoadedCapabilities.ROSTER})

        membership_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/memberships"
        )
        parsed_membership_resp = BeautifulSoup(membership_resp.text, "html.parser")

        authenticity_token = parsed_membership_resp.find("meta", attrs={"name": "csrf-token"}).get(
            "content"
        )
        remove_params = {"_method": "delete", "authenticity_token": authenticity_token}
        remove_resp = self.session.post(
            "https://www.gradescope.com/courses/"
            + self.cid
            + "/memberships/"
            + self.roster[name].data_id,
            data=remove_params,
            headers={"x-csrf-token": authenticity_token},
        )

        # TODO this is highly wasteful, need to likely improve this.
        self.roster = {}
        self._lazy_load_roster()

    def get_assignments(self):
        assignments_resp = self.session.get("https://www.gradescope.com/courses/" + self.cid + '/assignments')
        parsed = BeautifulSoup(assignments_resp.text, "html.parser")

        if 'You are not authorized to access this page.' in parsed.text:
            assignments_resp = self.session.get("https://www.gradescope.com/courses/" + self.cid)
            parsed = BeautifulSoup(assignments_resp.text, "html.parser")

        assignments_table = parsed.find("table", id="assignments-student-table")
        if not assignments_table:
            assignments_table = parsed.find("table", id="assignments-instructor-table")

        assignments_table_body = assignments_table.find("tbody")

        datefmt = "%Y-%m-%d %H:%M:%S %z"

        assignments = []

        for row in assignments_table_body.find_all("tr"):            
            name = row.find("th", class_="table--primaryLink")

            if not name:
                name = row.find("div", class_="assignments--rowTitle")
                assign_id = name.find('a').get('href').split('/')[-1]
            else:
                assign_id = name.find('a').get('href').split('/')[-1]
            name = name.text

            timeline_cols = row.find_all("td", {"class": "table--hiddenColumn"})

            if not timeline_cols or len(timeline_cols) == 0:
                timeline_cols = row.find_all("td", {"class": "hidden-column"})

            assigned = timeline_cols[0].text
            due = timeline_cols[1].text

            if assigned is None or assigned == "" or 'false' in assigned:
                assigned = None
            else:
                assigned = datetime.strptime(assigned, datefmt)

            if due is None or due == "":
                due = None
            else:
                due = datetime.strptime(due, datefmt)

            assignments.append( {
                    "id": assign_id,
                    "name": name,
                    "assigned": assigned,
                    "due": due,
                })

        return assignments

    def change_person_role(self, name, role):
        self._check_capabilities({LoadedCapabilities.ROSTER})

        membership_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/memberships"
        )
        parsed_membership_resp = BeautifulSoup(membership_resp.text, "html.parser")

        authenticity_token = parsed_membership_resp.find("meta", attrs={"name": "csrf-token"}).get(
            "content"
        )
        role_params = {
            "course_membership[role]": role.value,
        }
        role_resp = self.session.patch(
            "https://www.gradescope.com/courses/"
            + self.cid
            + "/memberships/"
            + self.roster[name].data_id
            + "/update_role",
            data=role_params,
            headers={"x-csrf-token": authenticity_token},
        )

        # TODO this is highly wasteful, need to likely improve this.
        self.roster = {}
        self._lazy_load_roster()

    # ~~~~~~~~~~~~~~~~~~~~~~ASSIGNMENTS~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add_assignment(
        self,
        name,
        release,
        due,
        template_file,
        student_submissions=True,
        late_submissions=False,
        group_submissions=0,
    ):
        self._check_capabilities({LoadedCapabilities.ASSIGNMENTS})

        assignment_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/assignments"
        )
        parsed_assignment_resp = BeautifulSoup(assignment_resp.text, "html.parser")
        authenticity_token = parsed_assignment_resp.find("meta", attrs={"name": "csrf-token"}).get(
            "content"
        )

        # TODO Make this less brittle and make sure to support all options properly
        assignment_params = {
            "authenticity_token": authenticity_token,
            "assignment[title]": name,
            "assignment[student_submission]": student_submissions,
            "assignment[release_date_string]": release,
            "assignment[due_date_string]": due,
            "assignment[allow_late_submissions]": 1 if late_submissions else 0,
            "assignment[submission_type]": "image",  # TODO What controls this?
            "assignment[group_submission]": group_submissions,
        }
        assignment_files = {"template_pdf": open(template_file, "rb")}
        assignment_resp = self.session.post(
            "https://www.gradescope.com/courses/" + self.cid + "/assignments",
            files=assignment_files,
            data=assignment_params,
        )

        # TODO this is highly wasteful, need to likely improve this.
        self.assignments = {}
        self._lazy_load_assignments()

    def remove_assignment(self, name):
        self._check_capabilities({LoadedCapabilities.ASSIGNMENTS})

        assignment_resp = self.session.get(
            "https://www.gradescope.com/courses/"
            + self.cid
            + "/assignments/"
            + self.assignments[name].aid
            + "/edit"
        )
        parsed_assignment_resp = BeautifulSoup(assignment_resp.text, "html.parser")
        authenticity_token = parsed_assignment_resp.find("meta", attrs={"name": "csrf-token"}).get(
            "content"
        )

        remove_params = {"_method": "delete", "authenticity_token": authenticity_token}

        remove_resp = self.session.post(
            "https://www.gradescope.com/courses/"
            + self.cid
            + "/assignments/"
            + self.assignments[name].aid,
            data=remove_params,
        )

        # TODO this is highly wasteful, need to likely improve this.
        self.assignments = {}
        self._lazy_load_assignments()

    # ~~~~~~~~~~~~~~~~~~~~~~HOUSEKEEPING~~~~~~~~~~~~~~~~~~~~~~~~~

    def _lazy_load_assignments(self):
        """
        Load the assignment dictionary from assignments. This is done lazily to avoid slowdown caused by getting
        all the assignments for all classes. Also makes us less vulnerable to blocking.
        """
        assignment_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/assignments"
        )
        parsed_assignment_resp = BeautifulSoup(assignment_resp.text, "html.parser")

        assignment_table = []
        for assignment_row in parsed_assignment_resp.findAll(
            "tr", class_="js-assignmentTableAssignmentRow"
        ):
            row = []
            for td in assignment_row.findAll("td"):
                row.append(td)
            assignment_table.append(row)

        for row in assignment_table:
            name = row[0].text
            aid = row[0].find("a").get("href").rsplit("/", 1)[1]
            points = row[1].text
            # TODO: (released,due) = parse(row[2])
            submissions = row[3].text
            percent_graded = row[4].text
            complete = True if "workflowCheck-complete" in row[5].get("class") else False
            regrades_on = False if row[6].text == "OFF" else True
            # TODO make these types reasonable
            self.assignments[name] = GSAssignment(
                name, aid, points, percent_graded, complete, regrades_on, self
            )
        self.state.add(LoadedCapabilities.ASSIGNMENTS)
        pass

    def _lazy_load_roster(self):
        """
        Load the roster list  This is done lazily to avoid slowdown caused by getting
        all the rosters for all classes. Also makes us less vulnerable to blocking.
        """
        membership_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/memberships"
        )
        parsed_membership_resp = BeautifulSoup(membership_resp.text, "html.parser")

        if "You are not authorized to access this page" in membership_resp.text:
            print ('No access to roster, skipping')
            return
        else:
            print("Instructor access to roster")

        roster_table = []
        for student_row in parsed_membership_resp.find_all("tr", class_="rosterRow"):
            row = []
            for td in student_row("td"):
                row.append(td)
            roster_table.append(row)

        for row in roster_table:
            name = row[0].text.rsplit(" ", 1)[0]
            data_id = row[0].find("button", class_="rosterCell--editIcon").get("data-id")
            if len(row) >= 4 and row[2].find("option", selected="selected"):
                email = row[1].text
                role = row[2].find("option", selected="selected").text
                submissions = int(row[3].text)
                linked = True if "statusIcon-active" in row[4].find("i").get("class") else False
            else:
                email = row[2].text
                role = row[3].find("option", selected="selected").text
                if len(row[5].text):
                    submissions = int(row[5].text)
                    linked = True if "statusIcon-active" in row[6].find("i").get("class") else False
                else:
                    submissions = int(row[4].text)
                    linked = True if "statusIcon-active" in row[5].find("i").get("class") else False
            # TODO Make types reasonable.
            self.roster[name] = GSPerson(name, data_id, email, role, submissions, linked)
        self.state.add(LoadedCapabilities.ROSTER)

    def _check_capabilities(self, needed):
        """
        checks if we have the needed data loaded and gets them lazily.
        """
        missing = needed - self.state
        if LoadedCapabilities.ASSIGNMENTS in missing:
            self._lazy_load_assignments()
        if LoadedCapabilities.ROSTER in missing:
            self._lazy_load_roster()

    def delete(self):
        course_edit_resp = self.session.get(
            "https://www.gradescope.com/courses/" + self.cid + "/edit"
        )
        parsed_course_edit_resp = BeautifulSoup(course_edit_resp.text, "html.parser")

        authenticity_token = parsed_course_edit_resp.find("meta", attrs={"name": "csrf-token"}).get(
            "content"
        )

        print(authenticity_token)

        delete_params = {"_method": "delete", "authenticity_token": authenticity_token}
        print(delete_params)

        delete_resp = self.session.post(
            "https://www.gradescope.com/courses/" + self.cid,
            data=delete_params,
            headers={
                "referer": "https://www.gradescope.com/courses/" + self.cid + "/edit",
                "origin": "https://www.gradescope.com",
            },
        )

        # TODO make this less brittle
