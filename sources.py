import streamlit as st
import pandas as pd
import json
from datetime import datetime
from status_tests import now, date_format

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
def get_submissions(do_all = False) -> pd.DataFrame:
    # SID is useless because it is the Penn student ID *but can be null*
    if not do_all:
        return pd.read_csv('gs_submissions.csv')[['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','Sections','assign_id','First Name','Last Name']]
    else:
        return pd.read_csv('gs_submissions.csv').drop(columns=['SID','View Count', 'Submission Count'])

def get_assignments_and_submissions(courses_df: pd.DataFrame, assignments_df: pd.DataFrame, submissions_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Joins assignments and submissions, paying attention to course ID as well as assignment ID

    Also drops some duplicates
    '''
    return assignments_df.rename(columns={'name':'assignment', 'course_id':'crs'}).\
        merge(submissions_df, left_on=['assignment_id','crs'], right_on=['assign_id','course_id']).\
        merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['crs','course_id'])

def get_course_names():
    """
    Retrieve the (short) name of every course
    """
    return get_courses().drop_duplicates().rename(columns={'shortname':'Course'}).set_index('cid')['Course']

def get_course_enrollments():
    """
    Information about each course, students, and submissions
    """
    enrollments = get_students().\
        merge(get_assignments_and_submissions(get_courses(), get_assignments(), get_submissions()), left_on='emails2', right_on='Email').\
        drop(columns=['course_id','year','course_id','assign_id','emails2','Submission ID'])

    enrollments = enrollments.sort_values(['due','assignment','Status','Total Score','Last Name','First Name'],
                                        ascending=[True,True,True,True,True,True])
    
    return enrollments


def get_course_student_status_summary(
        is_overdue, 
        is_near_due, 
        is_submitted) -> pd.DataFrame:
    """
    Returns the number of total, submissions, overdue, and pending
    """

    course_col = 'cid'
    # name = 'shortname'
    due_date = 'due'
    # student_id = 'sid'

    enrollments = get_course_enrollments()
    useful = enrollments.merge(get_courses().drop(columns=['shortname','name']),left_on='cid', right_on='cid').rename(columns={'shortname':'Course'})

    useful['😰'] = useful.apply(lambda x: is_overdue(x, datetime.strptime(x[due_date], date_format)), axis=1)
    useful['😅'] = useful.apply(lambda x: is_near_due(x, datetime.strptime(x[due_date], date_format)), axis=1)
    useful['✓'] = useful.apply(lambda x: is_submitted(x), axis=1)

    ids_to_short = enrollments[['cid','shortname']].drop_duplicates().rename(columns={'shortname':'Course'}).set_index('cid')

    return useful[[course_col,'😰','😅','✓']].groupby(course_col).sum().join(ids_to_short)[['Course','😰','😅','✓']]

