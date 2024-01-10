from enum import Enum
from python_canvas_layer.course_info import Person

class GSRole(Enum):
    STUDENT = 0
    INSTRUCTOR = 1
    TA = 2
    READER = 3
    
    def from_str(val):
        if isinstance(val, GSRole):
            return val
        strings = {
            'Instructor': GSRole.INSTRUCTOR,
            'Student': GSRole.STUDENT,
            'TA': GSRole.TA,
            'Reader': GSRole.READER
        }
        role =  strings.get(val)
        if role is not None:
            return role
        else:
            raise GSRoleException("Not a valid role string: " + role)  

    def to_str(val):
        strings = {
            GSRole.INSTRUCTOR : 'Instructor',
            GSRole.STUDENT : 'Student',
            GSRole.TA : 'TA',
            GSRole.READER : 'Reader'
        }
        return strings[val]
        
    class GSRoleException(Exception):
        pass
    
    
class GSPerson(Person):
    def __init__(self, name, data_id, email, role, submissions, linked, user_id, student_id):
        self.name = name
        self.data_id = data_id
        self.student_id = student_id
        self.email = email
        self.emails = [email]
        self.role = GSRole.from_str(role)
        self.linked = linked
        self.submissions = submissions
        self.user_id = user_id

