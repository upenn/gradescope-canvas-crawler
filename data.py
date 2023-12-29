import yaml
import sys, traceback
import sqlite3
import pandas as pd
import sqlalchemy
from sqlalchemy.sql import text
from datetime import datetime

include_gradescope_data = True
include_canvas_data = True

with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)

    if 'show' in config['canvas']:
        include_canvas_data = config['canvas']['show']
        print ('Canvas data: {}'.format(include_canvas_data))

    if 'show' in config['gradescope']:
        include_gradescope_data = config['gradescope']['show']
        print ('Gradescope data: {}'.format(include_gradescope_data))


# connection = sqlite3.connect("grades.db", check_same_thread=False)
dbEngine=sqlalchemy.create_engine('sqlite:///./dashboard.db') # ensure this is the correct path for the sqlite file. 

connection = dbEngine.connect()

def get_gs_students() -> pd.DataFrame:
    return pd.read_sql_table("gs_students", connection)

def get_canvas_students() -> pd.DataFrame:
    return pd.read_sql_table("canvas_students", connection)
    # return pd.read_csv('data/canvas_students.csv')

def get_aligned_students(include_gs: bool, include_canvas: bool) -> pd.DataFrame:
    with dbEngine.connect() as connection:
        if include_gs and include_canvas:
            courses = pd.read_sql(sql=text("""select cast(sid as int) as gs_student_id, cast(student_id as int) as student_id, 
                                           case when gs.name is not null then gs.name else sortable_name end as student, 
                                           case when emails is not null then emails else c.email end as email, cast(user_id as int) as gs_user_id, gs.course_id as gs_course_id, lti as canvas_course_id, c.id as canvas_sid
                                           from gs_students gs join gs_courses crs on gs.course_id=crs.cid full join canvas_students c on student_id = sis_user_id
                                           where role like "%STUDENT"
                                           """), con=connection)
        elif include_gs:
            courses = pd.read_sql(sql=text("""select cast(sid as int) as gs_student_id, cast(student_id as int) as student_id, gs.name as student, emails as email, cast(user_id as int) as gs_user_id, gs.course_id as gs_course_id, lti as canvas_course_id, null as canvas_sid
                                           from gs_students gs join gs_courses crs on gs.course_id=crs.cid
                                           where role like "%STUDENT"
                                           """), con=connection)
        else:
            courses = pd.read_sql(sql=text("""select null as gs_student_id, cast(sis_user_id as int) as student_id,sortable_name as student, email, null as gs_user_id, null as gs_course_id, course_id as canvas_course_id, c.id as canvas_sid
                                    from canvas_students c"""), con=connection)

        return courses

def get_gs_courses() -> pd.DataFrame:
    return pd.read_sql_table("gs_courses", connection)

def get_canvas_courses() -> pd.DataFrame:
    return pd.read_sql_table("canvas_courses", connection)
    # return pd.read_csv('data/canvas_courses.csv')

def get_aligned_courses(include_gs: bool, include_canvas: bool) -> pd.DataFrame:
    with dbEngine.connect() as connection:
        if include_gs and include_canvas:
            courses = pd.read_sql(sql=text("""select cid as gs_course_id, gs.name as gs_name, c.name as canvas_name, shortname, year as term, lti as canvas_course_id, sis_course_id, start_at, end_at
                                    from gs_courses gs full join canvas_courses c on gs.lti = c.id"""), con=connection)
        elif include_gs:
            courses = pd.read_sql(sql=text("""select cid as gs_course_id, gs.name as gs_name, null as canvas_name, shortname, year as term, lti as canvas_course_id, null as sis_course_id, null as start_at, null as end_at
                                    from gs_courses gs"""), con=connection)
        else:
            courses = pd.read_sql(sql=text("""select null as gs_course_id, null as gs_name, c.name as canvas_name, null as shortname, null as term, c.id as canvas_course_id, sis_course_id, start_at, end_at
                                    from canvas_courses gs"""), con=connection)
        
        courses['start_at'] = courses['start_at'].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") if not pd.isna(x) else None)
        courses['end_at'] = courses['end_at'].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") if not pd.isna(x) else None)
        
        return courses

def get_gs_assignments() -> pd.DataFrame:
    return pd.read_sql_table("gs_assignments", connection)

def get_canvas_assignments() -> pd.DataFrame:
    return pd.read_sql_table("canvas_assignments", connection)
    # return pd.read_csv('data/canvas_assignments.csv')

def get_aligned_assignments(include_gs: bool, include_canvas: bool) -> pd.DataFrame:
    with dbEngine.connect() as connection:
        if include_gs and include_canvas:
            assignments = pd.read_sql(sql=text("""select gs.id as gs_assignment_id, null as canvas_assignment_id, gs.course_id as gs_course_id, crs.lti as canvas_course_id, gs.name, strftime("%Y-%m-%dT%H:%M:%SZ", gs.assigned) as assigned, strftime("%Y-%m-%dT%H:%M:%SZ", gs.due) as due, null as canvas_max_points, "Gradescope" as source
                                                from gs_assignments gs join gs_courses crs on gs.course_id = crs.cid
                                                union
                                                select null as gs_assignment_id, c.id as canvas_assignment_id, null as gs_course_id, c.course_id as canvas_course_id, c.name as name, unlock_at as assigned, due_at as due, points_possible as canvas_max_points, "Canvas" as source
                                               from canvas_assignments c left join gs_courses crs on c.course_id = crs.lti
                                               """), con=connection)
        elif include_gs:
            assignments = pd.read_sql(sql=text("""select gs.id as gs_assignment_id, null as canvas_assignment_id, gs.course_id as gs_course_id, crs.lti as canvas_course_id, gs.name, strftime("%Y-%m-%dT%H:%M:%SZ", gs.assigned) as assigned, strftime("%Y-%m-%dT%H:%M:%SZ", gs.due) as due, null as canvas_max_points, "Gradescope" as source
                                    from gs_assignments gs join gs_courses crs on gs.course_id = crs.cid
                                    """), con=connection)
        else:
            assignments = pd.read_sql(sql=text("""select null as gs_assignment_id, c.id as canvas_assignment_id, null as gs_course_id, c.course_id as canvas_course_id, c.name as name, unlock_at as assigned, due_at as due, points_possible as canvas_max_points, "Canvas" as source
                                    from canvas_assignments c"""), con=connection)

        assignments['due'] = assignments['due'].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") if not pd.isna(x) else None)
        assignments['assigned'] = assignments['assigned'].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") if not pd.isna(x) else None)

        return assignments

def get_gs_submissions() -> pd.DataFrame:
    return pd.read_sql_table("gs_submissions", connection)

def get_canvas_submissions() -> pd.DataFrame:
    return pd.read_sql_table("canvas_submissions", connection)
    # return pd.read_csv('data/canvas_submissions.csv', low_memory=False)

def get_gs_extensions() -> pd.DataFrame:
    return pd.read_sql_table("gs_extensions", connection)

def get_canvas_extensions() -> pd.DataFrame:
    return pd.read_sql_table("canvas_extensions", connection)
    # return pd.read_csv('data/canvas_extensions.csv')