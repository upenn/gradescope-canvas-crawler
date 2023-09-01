import streamlit as st

import datetime
import pandas as pd
import numpy as np
import json
import pytz
from datetime import timezone, timedelta

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

@st.cache_data
def get_submissions() -> pd.DataFrame:
    # SID is useless because it is the Penn student ID *but can be null*
    return pd.read_csv('gs_submissions.csv')[['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','assign_id','First Name','Last Name']]

def get_assignments_and_submissions(assignments_df: pd.DataFrame, submissions_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Joins assignments and submissions, paying attention to course ID as well as assignment ID

    Also drops some duplicates
    '''
    return assignments_df.rename(columns={'name':'assignment', 'course_id':'crs'}).\
        merge(submissions_df, left_on=['assignment_id','crs'], right_on=['assign_id','course_id']).\
        merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['crs','course_id','shortname'])


####
## Reference time, in our time zone
now = datetime.datetime.now()
now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute,now.second,now.microsecond, tzinfo=timezone(offset=timedelta()))
date_format = '%Y-%m-%d %H:%M:%S%z'


#####################################################
##
## Load data from crawler daemon job
##
students_df = get_students()
courses_df = get_courses()
submissions_df = get_submissions()
assignments_df = get_assignments()

####################
## Join submissions with students.
## We have to do this not on student ID but on email address.
## It's very possible to have null student IDs
enrollments = students_df.\
    merge(get_assignments_and_submissions(assignments_df,submissions_df), left_on='emails2', right_on='Email').\
    drop(columns=['course_id','year','course_id','assign_id','emails2','Submission ID'])

def is_unsubmitted(x):
    return x['Status'] == 'Missing' or x['Total Score'] is None or x['Total Score'] < x['Max Points'] / 2.0 

def is_overdue(x, due):
    return is_unsubmitted(x) and due < now

def is_near_due(x, due):
    return is_unsubmitted(x) and (due - now) < timedelta(days = 7)

enrollments = enrollments.sort_values(['due','assignment','Status','Total Score','Last Name','First Name'])

for c,course in courses_df.iterrows():
    course_info = enrollments[enrollments['name']==course['name']]
    #assigns = course_info['assignment'].drop_duplicates()
    assigns = assignments_df[assignments_df['course_id']==course['cid']]
    st.subheader("Status of %s:"%course['name'])
    
    for a,assign in assigns.iterrows():
        df = course_info[course_info['assignment_id']==assign['assignment_id']].\
            drop(columns=['sid','cid','assignment_id','assignment','Last Name','First Name'])
        
        assigned = list(df['assigned'].drop_duplicates())[0]
        due = list(df['due'].drop_duplicates())[0]
        assigned_date = datetime.datetime.strptime(assigned, date_format)
        due_date = datetime.datetime.strptime(due, date_format)

        # Skip if it's not yet assigned!
        if now < assigned_date:
            continue

        st.markdown('### %s'%assign['name'])
        st.write('released on %s and due on %s'%(assigned,due))

        #,'assigned','due'

        st.dataframe(df.style.apply(
            lambda x: [f"background-color:pink" if is_overdue(x, due_date) else f'background-color:mistyrose' if is_near_due(x, due_date) else '' for i in x],
            axis=1), use_container_width=True,hide_index=True,
                    column_config={'name':None,'sid':None,'cid':None,'assign_id':None,'Last Name':None,'First Name':None, 'assigned':None,'due': None})
    st.divider()
