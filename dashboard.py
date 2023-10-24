import streamlit as st
from streamlit import column_config
from st_aggrid import AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from st_aggrid import GridOptionsBuilder, GridUpdateMode, DataReturnMode, AgGridTheme
import aggrid_helper

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

#@st.cache_data
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
        merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['crs','course_id'])


####
## Reference time, in our time zone
now = datetime.datetime.now()
#now = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute,now.second,now.microsecond, tzinfo=timezone(offset=timedelta()))
date_format = '%Y-%m-%d %H:%M:%S'


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
    return is_unsubmitted(x) and (due - now) < timedelta(days = 2)

def is_submitted(x):
    return x['Status'] != 'Missing'

def display_course(course_filter: pd.DataFrame):
    """
    Given a course datframe (with a singleton row), displays for each assignment (in ascending order of deadline):
    - a line chart of submissions over time
    - a table of students, with color coding for overdue, near due, and submitted
    """
    course = courses_df[courses_df['shortname']==course_filter].iloc[0]
    course_info = enrollments[enrollments['shortname']==course['shortname']]
    #assigns = course_info['assignment'].drop_duplicates()
    assigns = assignments_df[assignments_df['course_id']==course['cid']].copy().dropna()
    st.subheader("Status of %s:"%course['shortname'])

    assigns['due'] = assigns['due'].apply(lambda x:pd.to_datetime(x) if x else None)
    assigns = assigns.sort_values('due',ascending=True)

    for a,assign in assigns.iterrows():
        df = course_info[course_info['assignment_id']==assign['assignment_id']].\
            drop(columns=['sid','cid','assignment_id','assignment','Last Name','First Name'])
        
        assigned = list(df['assigned'].drop_duplicates())[0]
        due = list(df['due'].drop_duplicates())[0]
        assigned_date = datetime.datetime.strptime(assigned, date_format)
        due_date = datetime.datetime.strptime(due, date_format)

        with st.container():
            # Skip homework if it's not yet assigned!
            if now < assigned_date:
                continue

            st.markdown('### %s'%assign['name'])
            # st.write('released on %s and due on %s'%(assigned,due))
            st.write('Due on %s'%(due_date.strftime('%A, %B %d, %Y')))

            col1, col2 = st.tabs(['Students','Submissions by time'])#columns(2)

            by_time = df.copy().dropna()
            by_time['Submission Time'] = by_time['Submission Time'].apply(lambda x:pd.to_datetime(x) if x else None)
            # by_time['Submission Time'] = by_time['Submission Time'].apply(lambda x: 
            #                                                                 datetime.datetime(x.year,x.month,x.day,0,0,0,0,tzinfo=timezone(offset=timedelta())) 
            #                                                                 if x.year > 0 else None)
            by_time = by_time.set_index(pd.DatetimeIndex(by_time['Submission Time']))

            # by_time = df.groupby('Submission Time').count().reset_index()
            by_time = by_time.groupby(pd.Grouper(freq='1D', label='right')).count()
            by_time = by_time[['Submission Time','Total Score']].rename(columns={'Submission Time': 'Day', 'Total Score':'Count'})
            with col2:
                # st.write("Submissions over time:")
                st.line_chart(data=by_time,x='Day',y='Count')

            late_df = df[df.apply(lambda x: is_overdue(x, due_date), axis=1)]['Email']
            late_as_list = str(late_df.to_list())[1:-2].replace('\'','').replace(' ','')
            
            last_minute_df = df[df.apply(lambda x: is_near_due(x, due_date), axis=1)]['Email']
            last_minute_as_list = str(last_minute_df.to_list())[1:-2].replace('\'','').replace(' ','')

            with col1:
                # st.write("Students and submissions:")
                st.dataframe(df.style.format(precision=0).apply(
                    lambda x: [f"background-color:pink" 
                                if is_overdue(x, due_date) 
                                else f'background-color:mistyrose' 
                                    if is_near_due(x, due_date) 
                                    else 'background-color:lightgreen' if is_submitted(x) else '' for i in x],
                    axis=1), use_container_width=True,hide_index=True,
                            column_config={
                                'name':None,'sid':None,'cid':None,
                                'assign_id':None,'Last Name':None,'First Name':None, 
                                'assigned':None,'due': None,
                                'shortname':None,
                                'Total Score':st.column_config.NumberColumn(step=1,format="$%d"),
                                'Max Points':st.column_config.NumberColumn(step=1,format="$%d"),
                                # 'Submission Time':st.column_config.DatetimeColumn(format="D MM YY, h:mm a")
                                })
                
                if len(late_df) > 0:
                    URL_STRING = "mailto:" + late_as_list + "?subject=Late homework&body=Hi, we have not received your submission for " + assign['name'] + " for " + course['name'].strip() + ". Please let us know if you need special accommodation."

                    st.markdown(
                        f'<a href="{URL_STRING}" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Email late students</a>',
                        unsafe_allow_html=True
                    )
                if len(last_minute_df) > 0:
                    URL_STRING = "mailto:" + last_minute_as_list + "?subject=Approaching deadline&body=Hi, as a reminder, " + assign['name'] + " for " + course['name'].strip() + " is nearly due. Please let us know if you need special accommodation."

                    st.markdown(
                        f'<a href="{URL_STRING}" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Email reminder about deadline</a>',
                        unsafe_allow_html=True
                    )
    st.divider()


enrollments = enrollments.sort_values(['due','assignment','Status','Total Score','Last Name','First Name'],
                                      ascending=[True,True,True,True,True,True])

st.markdown("# Penn CIS Gradescope-Canvas Dashboard")
# Inject custom CSS to set the width of the sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 450px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)
with st.sidebar:
    birds_eye = []
    for i, course in courses_df.iterrows():
        course_info = enrollments[enrollments['name']==course['name']]

        overdue = course_info[course_info.apply(lambda x: is_overdue(x, datetime.datetime.strptime(x['due'], date_format)), axis=1)].count()['sid']
        pending = course_info[course_info.apply(lambda x: is_near_due(x, datetime.datetime.strptime(x['due'], date_format)), axis=1)].count()['sid']
        submitted = course_info[course_info.apply(lambda x: is_submitted(x), axis=1)].count()['sid']

        overall_df = pd.DataFrame([{'Course':course['shortname'],"😅":pending,"😰":overdue, "✓":submitted}])
        birds_eye.append(overall_df)

    birds_eye_df = pd.concat(birds_eye)
    birds_eye_df.style.apply(
                lambda x: [f"background-color:pink" 
                            if overdue >0
                            else f'background-color:mistyrose' 
                                if pending >0
                                else 'background-color:lightgreen' for i in x],
                axis=1)
    
 
    gb = GridOptionsBuilder.from_dataframe(birds_eye_df)
                
    #### Add hyperlinks
    # gb.configure_column(
    #     "Course",
    #     headerName="Course",
    #     width=100,
    #     cellRenderer=aggrid_helper.add_url('Course', '/#status-of-cis-5450-2023-fall-big-data-analytics-on-campus')
    # )
    other_options = {'suppressColumnVirtualisation': True}
    gb.configure_grid_options(**other_options)

    gridOptions = gb.build()
    gridOptions['getRowStyle'] = aggrid_helper.add_highlight('params.data["😅"] > 0 || params.data["😰"] > 0', 'black', 'mistyrose')

    st.write("Overall status:")
    grid = AgGrid(
        birds_eye_df,
        gridOptions=gridOptions,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True
        )



## TODO: summary list of heavily overdue with mailto links?

course_filter = st.selectbox("Select course", pd.unique(courses_df["shortname"]))

# for c,course in courses_df.iterrows():

display_course(course_filter=course_filter)