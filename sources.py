import streamlit as st
import pandas as pd
import json
from datetime import datetime

now = datetime.now()
#now = datetime(now.year, now.month, now.day, now.hour, now.minute,now.second,now.microsecond, tzinfo=timezone(offset=timedelta()))
date_format = '%Y-%m-%d %H:%M:%S'


@st.cache_data
def get_courses() -> pd.DataFrame:
    return pd.read_csv('gs_courses.csv')

@st.cache_data
def get_students() -> pd.DataFrame:
    students_df = pd.read_csv('gs_students.csv').rename(columns={'name':'student'})
    students_df['emails2'] = students_df['emails'].apply(lambda x: json.loads(x.replace('\'','"')) if x else None)
    students_df = students_df.explode('emails2').drop(columns=['emails'])
    return students_df

@st.cache_data
def get_assignments() -> pd.DataFrame:
    return pd.read_csv('gs_assignments.csv').rename(columns={'id':'assignment_id'})

#@st.cache_data
def get_submissions() -> pd.DataFrame:
    # SID is useless because it is the Penn student ID *but can be null*
    return pd.read_csv('gs_submissions.csv')[['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','assign_id','First Name','Last Name']]

def get_assignments_and_submissions(courses_df: pd.DataFrame, assignments_df: pd.DataFrame, submissions_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Joins assignments and submissions, paying attention to course ID as well as assignment ID

    Also drops some duplicates
    '''
    return assignments_df.rename(columns={'name':'assignment', 'course_id':'crs'}).\
        merge(submissions_df, left_on=['assignment_id','crs'], right_on=['assign_id','course_id']).\
        merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['crs','course_id'])

def get_course_student_status(df: pd.DataFrame, course: str, name: str, due_date: str, student_id:str, is_overdue, is_near_due, is_submitted) -> pd.DataFrame:
    """
    Returns the number of total, submissions, overdue, and pending
    """

    useful = df.copy().rename(columns={'shortname':'Course'})
    useful['😅'] = useful.apply(lambda x: is_overdue(x, datetime.strptime(x[due_date], date_format)), axis=1)
    useful['😰'] = useful.apply(lambda x: is_near_due(x, datetime.strptime(x[due_date], date_format)), axis=1)
    useful['✓'] = useful.apply(lambda x: is_submitted(x), axis=1)

    ids_to_short = df[['cid','shortname']].drop_duplicates().rename(columns={'shortname':'Course'}).set_index('cid')

    return useful[[course,'😅','😰','✓']].groupby(course).sum().join(ids_to_short)[['Course','😅','😰','✓']]
