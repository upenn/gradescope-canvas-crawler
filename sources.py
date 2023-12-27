import streamlit as st
import pandas as pd
import json
from datetime import datetime
from dateutil.tz import *
from status_tests import now, date_format

timezone = datetime.now().astimezone().tzinfo
# offset = timezone.utcoffset(datetime.now())
# tzoffset = f"{offset.days * 24 + offset.seconds // 3600:+03d}:{offset.seconds % 3600 // 60:02d}"

include_gradescope_data = True
include_canvas_data = True

@st.cache_data
def get_courses() -> pd.DataFrame:
    if include_gradescope_data:
        full_courses_gs = pd.read_csv('data/gs_courses.csv')

    if not include_canvas_data:
        return full_courses_gs.rename(columns={'lti': 'canvas_id'})
    
    full_courses_canvas = pd.read_csv('data/canvas_courses.csv').rename(columns={'id':'canvas_id', 'name': 'canvas_name'})
    full_courses_canvas = full_courses_canvas[full_courses_canvas['workflow_state'] == 'available'].\
        drop(columns=['is_public','workflow_state','start_at','end_at'])

    if include_gradescope_data:
        return full_courses_gs.merge(full_courses_canvas, left_on='lti', right_on='canvas_id', how='outer').\
            drop(columns=['lti','canvas_name'])
    else:
        return full_courses_canvas

@st.cache_data
def get_students() -> pd.DataFrame:
    if include_gradescope_data:
        students_df = pd.read_csv('data/gs_students.csv').rename(columns={'name':'student'})
        students_df['emails2'] = students_df['emails'].apply(lambda x: json.loads(x.replace('\'','"')) if x else None)
        students_df = students_df[students_df['role'] == 'GSRole.STUDENT']
        students_df = students_df.explode('emails2').drop(columns=['emails','role'])
        canvas_mappings_df = pd.read_csv('data/gs_courses.csv')[['cid','lti']].rename(columns={'cid':'gs_course_id'})


    # st.dataframe(students_df)

    if include_canvas_data:
        students_2_df = pd.read_csv('data/canvas_students.csv').rename(columns={'name':'canvas_student','id':'canvas_sid', 'course_id':'canvas_cid'})

    if include_canvas_data and include_gradescope_data:
        total = students_df.merge(canvas_mappings_df, left_on='course_id', right_on='gs_course_id').\
            merge(students_2_df, left_on=['student_id','lti'], right_on=['sis_user_id','canvas_cid'], how='outer').\
            drop(columns=['sortable_name','sis_user_id', 'created_at', 'canvas_cid','email','canvas_student','login_id', 'lti'])
    elif include_gradescope_data:
        total = students_df
    else:
        total = students_2_df
    
    # st.dataframe(total)

    return total

@st.cache_data
def get_assignments() -> pd.DataFrame:
    # TODO: how do we merge homeworks??

    courses = get_courses()
    if include_canvas_data:
        canvas = pd.read_csv('data/canvas_assignments.csv').\
            rename(columns={'id':'assignment_id', 'unlock_at': 'assigned', 'due_at': 'due'}).\
            drop(columns=['lock_at', 'muted', 'allowed_attempts'])
        canvas = canvas[canvas['course_id'].isin(courses['canvas_id'])].\
            rename(columns={'course_id':'canvas_course_id'}).\
            merge(courses[['canvas_id','cid']], left_on='canvas_course_id', right_on='canvas_id', how='left').drop(columns=['canvas_course_id'])
        canvas['source'] = 'Canvas'

        # st.dataframe(canvas)
    
    if include_gradescope_data:
        gs = pd.read_csv('data/gs_assignments.csv').rename(columns={'id':'assignment_id'}).\
            merge(courses[['cid','canvas_id']], left_on='course_id', right_on='cid', how='left').drop(columns='course_id')
        gs['source'] = 'Gradescope'
        # st.dataframe(gs)

    if include_canvas_data and include_gradescope_data:
        ret = pd.concat([gs, canvas])
        # st.dataframe(ret)
        return ret
    elif include_gradescope_data:
        return gs
    elif include_canvas_data:
        return canvas

@st.cache_data
def get_submissions(do_all = False) -> pd.DataFrame:
    # SID is useless because it is the Penn student ID *but can be null*
    if not do_all:
        return pd.read_csv('data/gs_submissions.csv')[['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','Sections','assign_id','First Name','Last Name']]
    else:
        return pd.read_csv('gs_submissions.csv').drop(columns=['SID','View Count', 'Submission Count'])

@st.cache_data
def get_extensions() -> pd.DataFrame:
    # TODO: how do we merge homework extensions??
    if include_gradescope_data:
        # duelate = 'Release (' + timezone + ')Due (' + timezone + ')'
        duelate = 'Release ({})Due ({})'.format(timezone, timezone)
        release = 'Release ({})'.format(timezone)
        due = 'Due ({})'.format(timezone)
        late = 'Late Due ({})'.format(timezone)
        extensions = pd.read_csv('data/gs_extensions.csv').\
            drop(columns=['Edit','Section', 'First & Last Name Swap', 'Last, First Name Swap', 'Sections', duelate, release, 'Time Limit'])

        extensions[due] = extensions[due].apply(lambda x: datetime.strptime(x, '%b %d %Y %I:%M %p') if x != '(no change)' and x != 'No late due date' and x != '--' and not pd.isnull(x) else None)
        extensions[late] = extensions[late].apply(lambda x: datetime.strptime(x, '%b %d %Y %I:%M %p') if x != '(no change)' and x != 'No late due date' and x != '--' and not pd.isnull(x) else None)
        
        return extensions
    elif include_canvas_data:
        return pd.read_csv('data/canvas_student_summaries.csv').rename(columns={'id':'extension_id', 'user_id':'SID', 'assignment_id':'assign_id', 'course_id':'course_id', 'extra_attempts':'Extra Attempts', 'extra_time':'Extra Time', 'extra_credit':'Extra Credit', 'late_due_at':'Late Due', 'extended_due_at':'Extended Due', 'created_at':'Created At', 'updated_at':'Updated At', 'workflow_state':'Workflow State', 'grader_id':'Grader ID', 'grader_notes':'Grader Notes', 'grader_visible_comment':'Grader Visible Comment', 'grader_anonymous_id':'Grader Anonymous ID', 'score':'Score', 'late':'Late', 'missing':'Missing', 'seconds_late':'Seconds Late', 'entered_score':'Entered Score', 'entered_grade':'Entered Grade', 'entered_at':'Entered At', 'excused':'Excused', 'posted_at':'Posted At', 'assignment_visible':'Assignment Visible', 'excuse':'Excuse', 'late_policy_status':'Late Policy Status', 'points_deducted':'Points Deducted', 'grading_period_id':'Grading Period ID', 'late_policy_deductible':'Late Policy Deductible', 'seconds_late_deduction':'Seconds Late Deduction', 'grading_period_title':'Grading Period Title', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_deductible':'Late Policy Deductible', 'seconds_late_deduction':'Seconds Late Deduction', 'grading_period_title':'Grading Period Title', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type'})

# @st.cache_data
# def get_submissions_ext(do_all = False) -> pd.DataFrame:
#     if include_gradescope_data:
#         # SID is useless because it is the Penn student ID *but can be null*
#         sub = get_submissions(do_all).merge(get_extensions(),left_on=['course_id','assign_id'], right_on=['course_id', 'assign_id'], how='left')
#         return sub
#     elif include_canvas_data:
#         return pd.read_csv('data/canvas_submissions.csv').rename(columns={'id':'Submission ID', 'user_id':'SID', 'submitted_at':'Submission Time'})

def get_assignments_and_submissions(courses_df: pd.DataFrame, assignments_df: pd.DataFrame, submissions_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Joins assignments and submissions, paying attention to course ID as well as assignment ID

    Also drops some duplicates
    '''

    st.dataframe(assignments_df)
    st.dataframe(submissions_df)
    st.dataframe(courses_df)

    return assignments_df.rename(columns={'name':'assignment', 'course_id':'crs'}).\
        merge(submissions_df, left_on=['assignment_id','crs'], right_on=['assign_id','course_id']).\
        merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['crs','course_id'])


def get_course_names():
    """
    Retrieve the (short) name of every course
    """
    return get_courses().drop_duplicates().dropna().rename(columns={'shortname':'Course'}).set_index('cid')['Course']

def get_course_enrollments():
    """
    Information about each course, students, and submissions
    """
    enrollments = get_students().\
        merge(get_assignments_and_submissions(get_courses(), get_assignments(), get_submissions()), left_on='emails2', right_on='Email').\
        drop(columns=['year','course_id','assign_id','emails2','Submission ID'])
    
    enrollments_with_exts = enrollments.\
        merge(get_extensions(), left_on=['user_id','assignment_id','cid'], right_on=['user_id','assign_id','course_id'], how='left').\
        drop(columns=['course_id', 'course_id'])

    enrollments_with_exts = enrollments_with_exts.sort_values(['due','assignment','Status','Total Score','Last Name','First Name'],
                                        ascending=[True,True,True,True,True,True])
    
    return enrollments_with_exts


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

