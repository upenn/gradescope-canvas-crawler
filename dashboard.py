import streamlit as st
from streamlit import column_config
from sources import get_assignments, get_course_names, get_courses, get_students, get_submissions, get_course_enrollments, get_course_student_status_summary
from sources import include_canvas_data, include_gradescope_data

from components import display_course, display_birds_eye, is_overdue
from status_tests import is_overdue, is_near_due, is_submitted, now, date_format

import yaml
import datetime
import pandas as pd

with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)

    if 'show' in config['canvas']:
        include_canvas_data = config['canvas']['show']
        print ('Canvas data: {}'.format(include_canvas_data))

    if 'show' in config['gradescope']:
        include_gradescope_data = config['gradescope']['show']
        print ('Gradescope data: {}'.format(include_gradescope_data))


name = ''
if include_gradescope_data:
    name = 'Gradescope'
if include_canvas_data:
    if len(name) > 0:
        name += '-'
    name += 'Canvas'

st.markdown("# Penn CIS {} Dashboard".format(name))
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