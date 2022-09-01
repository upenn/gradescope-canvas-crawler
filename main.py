from pyscope import pyscope as gs
from getpass import getpass
import os

from pyscope.account import GSAccount

email = os.environ.get("GS_EMAIL")
pwd = os.environ.get("GS_PWD")

conn = gs.GSConnection()

# Login
if email is None or pwd is None:
    email = input("Email: ")
    pwd = getpass("Password: ")

conn.login(email, pwd)

# Get Account
success = conn.get_account()
if not success:
    print("Failed to get account")
    exit(1)

acct: GSAccount = conn.account
course: gs.GSCourse = None

for course in acct.student_courses.values():
    assignments = course.get_assignments()
    print(assignments)
    break
