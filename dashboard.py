import streamlit as st
from streamlit import column_config
from sources import get_assignments, get_course_names, get_courses, get_students, get_submissions, get_course_enrollments, get_course_student_status_summary

from components import display_course, display_birds_eye, is_overdue
from status_tests import is_overdue, is_near_due, is_submitted, now, date_format

import datetime
import pandas as pd

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
    display_birds_eye(get_course_student_status_summary(
        is_overdue, is_near_due, is_submitted))

# Display the currently selected course contents
course_filter = st.selectbox("Select course", get_course_names())

display_course(course_filter=course_filter)