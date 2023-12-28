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
        return full_courses_gs.rename(columns={'lti': 'canvas_course_id', 'cid': 'gs_course_id'})
    
    full_courses_canvas = pd.read_csv('data/canvas_courses.csv').rename(columns={'id':'canvas_course_id', 'name': 'canvas_name'})
    full_courses_canvas = full_courses_canvas[full_courses_canvas['workflow_state'] == 'available'].\
        drop(columns=['is_public','workflow_state','start_at','end_at'])

    if include_gradescope_data:
        ret = full_courses_gs.merge(full_courses_canvas, left_on='lti', right_on='canvas_course_id', how='outer').\
            drop(columns=['lti']).rename(columns={'cid': 'gs_course_id'})
        
        ret['name'] = ret.apply(lambda x: x['canvas_name'] if pd.isna(x['name']) else x['name'], axis=1)
        return ret.drop(columns='canvas_name')
    else:
        full_courses_canvas['gs_course_id'] = None
        return full_courses_canvas.rename(columns={'canvas_name': 'name'})

@st.cache_data
def get_students() -> pd.DataFrame:
    if include_gradescope_data:
        students_df = pd.read_csv('data/gs_students.csv').rename(columns={'name':'student','sid':'gs_student_id', 'user_id': 'gs_user_id'})
        students_df['emails2'] = students_df['emails'].apply(lambda x: json.loads(x.replace('\'','"')) if x else None)
        students_df = students_df[students_df['role'] == 'GSRole.STUDENT']
        students_df = students_df.explode('emails2').drop(columns=['emails','role'])
        canvas_mappings_df = pd.read_csv('data/gs_courses.csv')[['cid','lti']].rename(columns={'cid':'gs_course_id'})


    # st.dataframe(students_df)

    if include_canvas_data:
        students_2_df = pd.read_csv('data/canvas_students.csv').rename(columns={'name':'canvas_student','id':'canvas_sid', 'course_id':'canvas_cid'})

    if include_canvas_data and include_gradescope_data:
        total = students_df.merge(canvas_mappings_df, left_on='course_id', right_on='gs_course_id').\
            drop(columns=['course_id']).\
            merge(students_2_df, left_on=['student_id','lti'], right_on=['sis_user_id','canvas_cid'], how='outer').\
            drop(columns=['sis_user_id', 'created_at', 'canvas_cid','canvas_student','login_id', 'lti'])
        
        total['student'] = total.apply(lambda x: x['student'] if not pd.isna(x['student']) else x['sortable_name'], axis=1)
        total['emails2'] = total.apply(lambda x: x['emails2'] if not pd.isna(x['emails2']) else x['email'], axis=1)
        total = total.drop(columns=['sortable_name', 'email']).rename(columns={'emails2':'email'})
    elif include_gradescope_data:
        total = students_df.rename(columns={'emails2':'email'})
    else:
        total = students_2_df.rename(columns={'emails2':'email'})
    
    # st.write('Students')
    # st.dataframe(total)

    return total

@st.cache_data
def get_assignments() -> pd.DataFrame:
    # TODO: how do we merge homeworks??

    courses = get_courses()
    if include_canvas_data:
        canvas = pd.read_csv('data/canvas_assignments.csv').\
            rename(columns={'id':'canvas_assignment_id', 'unlock_at': 'assigned', 'due_at': 'due', 'points_possible': 'canvas_max_points'}).\
            drop(columns=['lock_at', 'muted', 'allowed_attempts'])
        canvas = canvas[canvas['course_id'].isin(courses['canvas_course_id'])].\
            merge(courses[['canvas_course_id','gs_course_id']], left_on='course_id', right_on='canvas_course_id', how='left').drop(columns=['course_id'])
        canvas['source'] = 'Canvas'

        # st.dataframe(canvas)
    
    if include_gradescope_data:
        gs = pd.read_csv('data/gs_assignments.csv').rename(columns={'id':'gs_assignment_id'}).\
            merge(courses[['gs_course_id','canvas_course_id']], left_on='course_id', right_on='gs_course_id', how='left').drop(columns='course_id')
        gs['source'] = 'Gradescope'

    if include_canvas_data and include_gradescope_data:
        ret = pd.concat([gs, canvas]).rename(columns={'cid': 'gs_course_id'})
        # st.dataframe(ret)
        return ret
    elif include_gradescope_data:
        return gs.rename(columns={'cid': 'gs_course_id'})
    elif include_canvas_data:
        return canvas.rename(columns={'cid': 'gs_course_id'})

@st.cache_data
def get_submissions(do_all = False) -> pd.DataFrame:
    # SID is useless because it is the Penn student ID *but can be null*
    gs_sub = pd.read_csv('data/gs_submissions.csv')\
        [['Email','Total Score','Max Points','Status','Submission ID','Submission Time','Lateness (H:M:S)','course_id','Sections','assign_id']].\
        rename(columns={'assign_id': 'gs_assign_id_', 'course_id': 'gs_course_id_'})
    
    gs_sub = gs_sub.merge(get_students(), left_on=['Email','gs_course_id_'], 
                          right_on=['email', 'gs_course_id']).\
        drop(columns=['Email', 'gs_course_id_']).rename(columns={'canvas_sid': 'canvas_user_id'})
    
    canvas_sub = pd.read_csv('data/canvas_submissions.csv').\
        rename(columns={'id': 'canvas_sub_id', 'assignment_id': 'canvas_assign_id_', 'user_id': 'canvas_user_id', 'submitted_at': 'Submission Time', 'score': 'Total Score'})
    
    canvas_sub['Status'] = canvas_sub.apply(lambda x: "Missing" if x['missing'] else 'Graded' if not pd.isna(x['graded_at']) else 'Ungraded', axis=1)
    
    canvas_sub = canvas_sub.merge(get_students(), left_on=['canvas_user_id'],\
                                  right_on=['canvas_sid']).drop(columns=['canvas_sid', 'course_id', 'graded_at', 'grader_id', 'grade', 'entered_grade', 'entered_score', 'missing'])
    
    ## TODO: get Max Points by joining with the Canvas Assignment and getting its canvas_max_points
    canvas_sub = canvas_sub.merge(get_assignments()[['canvas_assignment_id', 'canvas_max_points', 'canvas_course_id']], left_on=['canvas_assign_id_'], right_on=['canvas_assignment_id']).drop(columns='canvas_assign_id_')

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

    # st.write('Courses')
    # st.dataframe(get_courses())
    # st.write('Students')
    # st.dataframe(get_students())
    # st.write('Assignments')
    # st.dataframe(get_assignments())
    st.write('Submissions')
    st.dataframe(get_submissions())

    gs_sub = assignments_df.\
        merge(submissions_df.rename(columns={'gs_course_id':'gs_course_id_'}), left_on=['gs_assignment_id','gs_course_id'], right_on=['gs_assign_id_','gs_course_id_']).\
        drop(columns=['gs_course_id']).\
        merge(courses_df,left_on='gs_course_id_', right_on='gs_course_id')#.drop(columns=['canvas_course_id','course_id'])

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
    return get_courses().drop_duplicates().dropna().rename(columns={'shortname':'Course'}).set_index('cid')['Course']

def get_course_enrollments():
    """
    Information about each course, students, and submissions
    """
    enrollments = get_students().\
        merge(get_assignments_and_submissions(get_courses(), get_assignments(), get_submissions()), left_on='email', right_on='Email').\
        drop(columns=['year','course_id','assign_id','Email','Submission ID'])
    
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

    course_col = 'gs_course_id'
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

