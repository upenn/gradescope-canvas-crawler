import streamlit as st
import pandas as pd
import yaml

from sources import get_students, get_courses, get_assignments, get_submissions, get_assignments_and_submissions

with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)

def get_scores_in_rubric(course = None) -> pd.DataFrame:
    st.markdown('## Rubric')

    courses = get_courses()
    if course is not None:
        courses = courses[courses['cid'] == course['cid']]

    for inx, course in courses.drop_duplicates().iterrows():
        # TODO: late??
        course_id = int(course['canvas_id'])

        # st.write('For course {}, {}'.format(course_id, course['name']))
        if course_id in config['rubric']:
            for group in config['rubric'][course_id]:
                st.write(group)
                the_course = courses[courses['cid'] == course['cid']]
                scores = get_submissions().\
                    merge(get_assignments().rename(columns={'name': 'assignment'}), \
                        left_on=['course_id','assign_id'], \
                        right_on=['course_id','assignment_id']).\
                            merge(the_course.drop(columns=['name','year']).rename(columns={'shortname':'course'}), \
                                left_on='course_id', right_on='cid')
                
                # st.dataframe(scores)

                assigns = scores[scores['assignment'].apply(lambda x: config['rubric'][course_id][group]['substring'] in x)]\
                        .groupby(by=['First Name', 'Last Name', 'Email']).\
                        sum().reset_index()\
                        [['First Name', 'Last Name', 'Total Score', "Max Points", 'Email']]

                st.dataframe(assigns)

                # TODO: in each iteration, rename "Max Points" to the group, and join with the set of students
                # based on Email