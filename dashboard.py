import streamlit as st

import datetime
import pandas as pd
import numpy as np
import json
import pytz
from datetime import timezone, timedelta

@st.cache_data
def get_courses():
    return pd.read_csv('gs_courses.csv')

@st.cache_data
def get_students():
    students_df = pd.read_csv('gs_students.csv').rename(columns={'name':'student'})
    students_df['emails2'] = students_df['emails'].apply(lambda x: json.loads(x.replace('\'','"')) if x else None)
    students_df = students_df.explode('emails2').drop(columns=['emails'])
    return students_df

@st.cache_data
def get_assignments():
    return pd.read_csv('gs_assignments.csv').rename(columns={'id':'assignment_id'})

@st.cache_data
def get_submissions():
    # SID is useless because it is the Penn student ID *but can be null*
    return pd.read_csv('gs_submissions.csv')[['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','assign_id','First Name','Last Name']]

students_df = get_students()

# st.write(students_df)
courses_df = get_courses()
# st.write(courses_df)
submissions_df = get_submissions()
# st.write(submissions_df)
assignments_df = get_assignments()
# st.write(assignments_df)

# assignments (id, course_id)  --> submission (assign_id, course_id)

sub_df = assignments_df.rename(columns={'name':'assignment', 'course_id':'crs'}).\
    merge(submissions_df, left_on=['assignment_id','crs'], right_on=['assign_id','course_id']).\
    merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['crs','course_id','shortname'])

# st.write(sub_df)

enrollments = students_df.\
    merge(sub_df, left_on='emails2', right_on='Email').\
    drop(columns=['course_id','year','course_id','assign_id','emails2','Submission ID'])

enrollments = enrollments.sort_values(['due','assignment','Status','Total Score','Last Name','First Name'])

now = datetime.datetime.now()
now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute,now.second,now.microsecond, tzinfo=timezone(offset=timedelta()))
date_format = '%Y-%m-%d %H:%M:%S%z'

for course in list(enrollments['name'].drop_duplicates()):
    course_info = enrollments[enrollments['name']==course]
    assigns = course_info['assignment'].drop_duplicates()
    st.subheader("Status of %s:"%course)
    for assign in list(assigns):
        df = course_info[course_info['assignment']==assign].\
            drop(columns=['sid','cid','assignment_id','assignment','Last Name','First Name'])
        
        assigned = list(df['assigned'].drop_duplicates())[0]
        due = list(df['due'].drop_duplicates())[0]
        assigned_date = datetime.datetime.strptime(assigned, date_format)
        due_date = datetime.datetime.strptime(due, date_format)

        # Skip if it's not yet assigned!
        if now < assigned_date:
            continue

        st.write('%s, released on %s and due on %s'%(assign,assigned,due))

        #,'assigned','due'

        st.dataframe(df.style.apply(
            lambda x: [f"background-color:mistyrose" 
                       if x['Status'] == 'Missing' or x['Total Score'] is None or x['Total Score'] < x['Max Points'] / 2.0 else '' for i in x],
            axis=1), use_container_width=True,hide_index=True,
                    column_config={'name':None,'sid':None,'cid':None,'assign_id':None,'Last Name':None,'First Name':None, 'assigned':None,'due': None})
    st.divider()
