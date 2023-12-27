import streamlit as st
import pandas as pd
import yaml

from sources import get_students, get_courses, get_assignments, get_submissions, get_assignments_and_submissions

with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)

def cap_points(row, rubric_items):
    actual_score = row['Total Score']
    max_score = row['Max Points']

    if actual_score > max_score and 'max_extra_credit' in rubric_items \
        and actual_score > max_score + rubric_items['max_extra_credit']:
        print(max_score)
        return max_score + rubric_items['max_extra_credit']
    else:
        print(actual_score)
        return actual_score

def adjust_max(row, rubric_items):
    max_score = row
    if 'max_score' in rubric_items and max_score > rubric_items['max_score']:
        max_score = rubric_items['max_score']

    return max_score

def sum_scaled(x, sums, maxes, scales):
    total = 0
    for i in range(len(sums)):
        if not pd.isnull(x[sums[i]]):
            total += x[sums[i]] * float(scales[i]) / float(x[maxes[i]])
    return total

def get_scores_in_rubric(output: callable, course:pd.Series = None) -> pd.DataFrame:
    courses = get_courses()
    if course is not None:
        courses = courses[courses['cid'] == course['cid']]

    for inx, course in courses.drop_duplicates().iterrows():
        # TODO: late??
        course_id = int(course['canvas_id'])

        # st.write('For course {}, {}'.format(course_id, course['name']))
        sums = []
        scales = []
        if course_id in config['rubric']:
            students = get_students()
            students = students[students['course_id'] == course['cid']]
            for group in config['rubric'][course_id]:
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
                
                if len(assigns):
                    assigns['Max Points'] = assigns['Max Points'].apply(lambda x: adjust_max(x, config['rubric'][course_id][group]))

                    # Cap the total points based on max + ec max
                    assigns['Total Score'] = assigns.apply(lambda x: cap_points(x, config['rubric'][course_id][group]), axis=1)

                students = students.merge(assigns[['Email', 'Total Score', 'Max Points']].rename(columns={'Total Score': group, 'Max Points': group + '_max'}), left_on='emails2', right_on='Email', how='left')\
                    .drop(columns=['Email'])

                sums.append(group)
                scales.append(config['rubric'][course_id][group]['points'])

                group_name = group[0].upper() + group[1:]
                if group_name[-1] >= '0' and group_name[-1] <= '9':
                    group_name = group_name[0:-1] + ' ' + group_name[-1]
                output(group_name, 'Total Score', 'Max Points', assigns.drop(columns=['Email']))

                # TODO: scale and sum the points

            students['Total Points'] = students.apply(lambda x: sum_scaled(x, sums, [s + "_max" for s in sums], scales), axis=1)
            students['Max Points'] = students.apply(lambda x: sum_scaled(x, [s + "_max" for s in sums], [s + "_max" for s in sums], scales), axis=1)
            output('Total', 'Total Points', 'Max Points', students)