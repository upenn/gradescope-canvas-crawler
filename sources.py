import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime
from dateutil.tz import *
from status_tests import now, date_format
from data import include_canvas_data, include_gradescope_data
from data import get_canvas_students, get_gs_students, get_gs_courses, get_canvas_courses
from data import get_gs_assignments, get_canvas_assignments, get_gs_submissions, get_canvas_submissions
from data import get_gs_extensions, get_canvas_extensions, get_aligned_courses, get_aligned_students
from data import get_aligned_assignments

timezone = datetime.now().astimezone().tzinfo
# offset = timezone.utcoffset(datetime.now())
# tzoffset = f"{offset.days * 24 + offset.seconds // 3600:+03d}:{offset.seconds % 3600 // 60:02d}"

@st.cache_data
def get_courses() -> pd.DataFrame:
    if include_gradescope_data:
        return get_aligned_courses(include_gradescope_data, include_canvas_data).rename(columns={'gs_name': 'name'})
    else:
        return get_aligned_courses(include_gradescope_data, include_canvas_data).rename(columns={'canvas_name': 'name'})

@st.cache_data
def get_students() -> pd.DataFrame:
    return get_aligned_students(include_gradescope_data, include_canvas_data)

@st.cache_data
def get_assignments() -> pd.DataFrame:
    return get_aligned_assignments(include_gradescope_data, include_canvas_data)

@st.cache_data
def get_submissions(do_all = False) -> pd.DataFrame:
    # SID is useless because it is the Penn student ID *but can be null*
    gs_sub = get_gs_submissions()\
        [['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','Sections','assign_id']].\
        rename(columns={'assign_id': 'gs_assign_id_', 'course_id': 'gs_course_id_'})
    
    gs_sub = gs_sub.merge(get_students(), left_on=['Email','gs_course_id_'], 
                          right_on=['email', 'gs_course_id']).\
        drop(columns=['Email', 'gs_course_id_','Sections']).rename(columns={'canvas_sid': 'canvas_user_id'})
    
    canvas_sub = get_canvas_submissions().\
        rename(columns={'id': 'canvas_sub_id', 'assignment_id': 'canvas_assign_id_', 'user_id': 'canvas_user_id', 'submitted_at': 'Submission Time', 'score': 'Total Score'})
    
    canvas_sub['Status'] = canvas_sub.apply(lambda x: "Missing" if x['missing'] else 'Graded' if not pd.isna(x['graded_at']) else 'Ungraded', axis=1)

    ## It looks like late_policy_status == 'none' or 'late' but late is also a bit set
    
    canvas_sub = canvas_sub.merge(get_students(), left_on=['canvas_user_id'],\
                                  right_on=['canvas_sid']).drop(columns=['canvas_sid', 'course_id', 'graded_at', 'grader_id', 'grade', 'entered_grade', 'entered_score', 'missing', 'excused', 'late_policy_status'])


    ## TODO: get Max Points by joining with the Canvas Assignment and getting its canvas_max_points
    canvas_sub = canvas_sub.merge(get_assignments()[['canvas_assignment_id', 'canvas_max_points', 'canvas_course_id']], left_on=['canvas_assign_id_'], right_on=['canvas_assignment_id']).drop(columns='canvas_assign_id_').\
    rename(columns={'canvas_max_points': 'Max Points'})

    ret = pd.concat([gs_sub, canvas_sub])
    return ret

@st.cache_data
def get_extensions() -> pd.DataFrame:
    # TODO: how do we merge homework extensions??
    if include_gradescope_data:
        # duelate = 'Release (' + timezone + ')Due (' + timezone + ')'
        duelate = 'Release ({})Due ({})'.format(timezone, timezone)
        release = 'Release ({})'.format(timezone)
        due = 'Due ({})'.format(timezone)
        late = 'Late Due ({})'.format(timezone)
        extensions = get_gs_extensions().\
            drop(columns=['Edit','Section', 'First & Last Name Swap', 'Last, First Name Swap', 'Sections', duelate, release, 'Time Limit','Extension Type'])

        extensions['Due'] = extensions[due].apply(lambda x: datetime.strptime(x, '%b %d %Y %I:%M %p') if x != '(no change)' and x != 'No late due date' and x != '--' and not pd.isnull(x) else None)
        extensions['Late'] = extensions[late].apply(lambda x: datetime.strptime(x, '%b %d %Y %I:%M %p') if x != '(no change)' and x != 'No late due date' and x != '--' and not pd.isnull(x) else None)

        extensions.drop(columns=[due, late], inplace=True)
        extensions.rename(columns={'course_id': 'gs_course_id_', 'assign_id': 'gs_assign_id_', 'user_id': 'gs_user_id_'}, inplace=True)
        # st.dataframe(extensions)
        
        return extensions
    elif include_canvas_data:
        return get_canvas_extensions().rename(columns={'id':'extension_id', 'user_id':'SID', 'assignment_id':'assign_id', 'course_id':'course_id', 'extra_attempts':'Extra Attempts', 'extra_time':'Extra Time', 'extra_credit':'Extra Credit', 'late_due_at':'Late Due', 'extended_due_at':'Extended Due', 'created_at':'Created At', 'updated_at':'Updated At', 'workflow_state':'Workflow State', 'grader_id':'Grader ID', 'grader_notes':'Grader Notes', 'grader_visible_comment':'Grader Visible Comment', 'grader_anonymous_id':'Grader Anonymous ID', 'score':'Score', 'late':'Late', 'missing':'Missing', 'seconds_late':'Seconds Late', 'entered_score':'Entered Score', 'entered_grade':'Entered Grade', 'entered_at':'Entered At', 'excused':'Excused', 'posted_at':'Posted At', 'assignment_visible':'Assignment Visible', 'excuse':'Excuse', 'late_policy_status':'Late Policy Status', 'points_deducted':'Points Deducted', 'grading_period_id':'Grading Period ID', 'late_policy_deductible':'Late Policy Deductible', 'seconds_late_deduction':'Seconds Late Deduction', 'grading_period_title':'Grading Period Title', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_deductible':'Late Policy Deductible', 'seconds_late_deduction':'Seconds Late Deduction', 'grading_period_title':'Grading Period Title', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type', 'late_policy_status':'Late Policy Status', 'missing_submission_type':'Missing Submission Type'})

@st.cache_data
def get_assignments_and_submissions(courses_df: pd.DataFrame, assignments_df: pd.DataFrame, submissions_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Joins assignments and submissions, paying attention to course ID as well as assignment ID

    Also drops some duplicates
    '''

    # st.write('Courses')
    # st.dataframe(get_courses())
    # st.write('Students')
    # st.dataframe(get_students())
    # st.write('Assignments')
    # st.dataframe(get_assignments())
    st.write('Submissions')
    st.dataframe(get_submissions())

    gs_sub = assignments_df.drop(columns=['canvas_course_id', 'canvas_assignment_id']).\
        merge(submissions_df.rename(columns={'gs_course_id':'gs_course_id_'}), left_on=['gs_assignment_id','gs_course_id'], right_on=['gs_assign_id_','gs_course_id_']).\
        drop(columns=['gs_course_id']).\
        merge(courses_df[['gs_course_id','name','sis_course_id']].rename(columns={'name': 'course_name'}),left_on='gs_course_id_', right_on='gs_course_id').\
        drop(columns=['gs_course_id_','gs_assign_id_','canvas_max_points'])
    
    # gs_sub['Email'] = gs_sub['email']

    # st.dataframe(gs_sub.head(100))

    # canvas_sub = assignments_df.rename(columns={'name':'assignment'}).\
    #     merge(submissions_df, left_on=['assignment_id','canvas_course_id'], right_on=['assign_id','course_id']).\
    #     merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['canvas_course_id','course_id'])

    return gs_sub#, canvas_sub])
# assignments_df.rename(columns={'name':'assignment'}).\
#         merge(submissions_df, left_on=['assignment_id','canvas_course_id'], right_on=['assign_id','course_id']).\
#         merge(courses_df,left_on='course_id', right_on='cid').drop(columns=['canvas_course_id','course_id'])


def get_course_names():
    """
    Retrieve the (short) name of every course
    """
    return get_courses().drop_duplicates().rename(columns={'shortname':'Course'}).set_index('gs_course_id')[['Course']].dropna()

@st.cache_data
def get_course_enrollments() -> pd.DataFrame:
    """
    Information about each course, students, and submissions along with extensions
    """
    enrollments = get_assignments_and_submissions(get_courses(), get_assignments(), get_submissions())

    # print(enrollments.dtypes)
    enrollments = enrollments.astype({'gs_user_id': int})
    # st.write('Enrollments')
    # st.dataframe(enrollments.head(5000))
    # print(get_extensions().dtypes)
    enrollments_with_exts = enrollments.\
        merge(get_extensions(), left_on=['gs_user_id','gs_assignment_id','gs_course_id'], right_on=['gs_user_id_','gs_assign_id_','gs_course_id_'], how='left').\
        drop(columns=['gs_course_id_','gs_assign_id_','gs_user_id_'])
    
    enrollments_with_exts.apply(lambda x: x['due'] if pd.isna(x['Due']) else x['Due'], axis=1)
    enrollments_with_exts.drop(columns=['Due','Late'], inplace=True)

    # st.write("With extensions")
    # st.dataframe(enrollments_with_exts.head(5000))

    enrollments_with_exts = enrollments_with_exts.sort_values(['due','name','Status','Total Score','student'],
                                        ascending=[True,True,True,True,True])
    
    return enrollments_with_exts


def get_course_student_status_summary(
        is_overdue, 
        is_near_due, 
        is_submitted) -> pd.DataFrame:
    """
    Returns the number of total, submissions, overdue, and pending
    """

    course_col = 'gs_course_id'
    # name = 'shortname'
    due_date = 'due'
    # student_id = 'sid'

    enrollments = get_course_enrollments()
    # st.dataframe(enrollments.head(100))

    useful = enrollments.rename(columns={'gs_course_id': 'gs_course_id_', 'canvas_course_id': 'canvas_course_id_'}).merge(get_courses().drop(columns=['shortname','name']),left_on='gs_course_id_', right_on='gs_course_id').rename(columns={'shortname':'Course'})

    useful['😰'] = useful.apply(lambda x: is_overdue(x, x['due']), axis=1)
    useful['😅'] = useful.apply(lambda x: is_near_due(x, x['due']), axis=1)
    useful['✓'] = useful.apply(lambda x: is_submitted(x), axis=1)

    ids_to_short = enrollments[['gs_course_id','course_name']].drop_duplicates().rename(columns={'course_name':'Course'}).set_index('gs_course_id')

    return useful[[course_col,'😰','😅','✓']].groupby(course_col).sum().join(ids_to_short)[['Course','😰','😅','✓']]

