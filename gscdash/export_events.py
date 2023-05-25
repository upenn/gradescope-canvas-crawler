from pyscope import pyscope as gs
from ics import Calendar, Event
import datetime
import os
import hashlib

from pyscope.account import GSAccount, GSCourse


def create_hw_events(course: GSCourse, assignment: dict) -> list:
    name = assignment["name"]
    # print(f"\tProcessing Assignment: {name}")

    assigned = assignment["assigned"]
    due = assignment["due"]

    date_printfmt = "%A, %d. %B %Y %I:%M%p"

    desc = f"""Course: {course.name}
Course Shortname: {course.shortname}
Link to Course: {course.get_url()}

Assignment: {name}
Assigned: {assigned.strftime(date_printfmt) if assigned is not None else "None"}
Due: {due.strftime(date_printfmt) if due is not None else "None"}"""

    out = []

    def hw_event(name:str, course_name:str, type, time):
        event = Event()
        event.name = f"{name} - {course_name} {type}"
        event.begin = time
        event.end = time
        event.description = desc

        hash = f"{name}{course_name}{time.strftime('%Y%m%d')}"
        hash = hashlib.sha1(hash.encode("utf-8")).hexdigest()
        event.uid = f"{hash}@cis.upenn.edu"
        return event

    if assigned is not None:
        out.append(hw_event(name, course.shortname, "Assigned", assigned))

    if due is not None:
        out.append(hw_event(name, course.shortname, "Due", due))

    return out


