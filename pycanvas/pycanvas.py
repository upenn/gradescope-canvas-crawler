#####################################################################################################################
##
## Copyright (C) 2022-23 by Zachary G. Ives
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
#####################################################################################################################

from canvasapi import Canvas
import pandas as pd
from course_info import CourseApi

class CanvasConnection(CourseApi):
    def __init__(self, canvas_url, canvas_key):
        self.canvas = Canvas(canvas_url, canvas_key)
        return
    
    def get_course(self, course_id):
        return self.canvas.get_course(course_id)

    def get_quizzes(course):
        quizzes = []
        for quiz in course.get_quizzes():
            quizzes.append({'id':quiz.id,'title':quiz.title,'published':quiz.published,\
                'unlock_at': quiz.unlock_at, 'due_at': quiz.due_at, 'lock_at': quiz.lock_at, 'published': quiz.published})

        return pd.DataFrame(quizzes)

    def get_modules(course):
        modules = []
        for module in course.get_modules():
            try:
                modules.append({
                    'id': module.id,
                    'name': module.name,
                    'published': module.published,
                    'unlock_at': module.unlock_at
                })
            except AttributeError:
                modules.append({
                    'id': module.id,
                    'name': module.name,
                    'unlock_at': module.unlock_at
                })

        return pd.DataFrame(modules)

    def get_module_items(course):
        module_items = []
        for module in course.get_modules():
            for item in module.get_module_items():
                details = {
                    'module_id': module.id,
                    'module_name': module.name,
                    'id': item.id,
                    'title': item.title,
                    # 'published': item.published,
                    'type': item.type,
                    'html_url': item.html_url
                }
                if item.type == 'Quiz':
                    details['url'] = item.url
                if item.type == 'ExternalUrl':
                    details['external_url'] = item.external_url

                try:
                    details['published'] = item['published']
                except:
                    pass
                module_items.append(details)
        return pd.DataFrame(module_items)

    def get_matching_module_url(module_items, index, typ):
        matches = module_items[module_items['title'].apply(lambda x: x.startswith(index))]
        if len(matches):
            matches = matches[matches['type'] == typ]
        if len(matches):
            if typ == 'Quiz':
                return matches['html_url'].array[0]
            else:
                return matches['external_url'].array[0]
