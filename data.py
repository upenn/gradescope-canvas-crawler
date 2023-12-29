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
                                    from gs_courses gs"""), con=connection)
        
        courses['start_at'] = courses['start_at'].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") if not pd.isna(x) else None)
        courses['end_at'] = courses['end_at'].apply(lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ") if not pd.isna(x) else None)
        
        return courses

def get_gs_assignments() -> pd.DataFrame:
    return pd.read_sql_table("gs_assignments", connection)

def get_canvas_assignments() -> pd.DataFrame:
    return pd.read_sql_table("canvas_assignments", connection)
    # return pd.read_csv('data/canvas_assignments.csv')

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