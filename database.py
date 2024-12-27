#####################################################################################################################
##
## Course Event Crawler - database access
##
## 
## Gradescope components are derived from Sagar Reddy Patil's Gradescope iCalendar Converter, 
## https://github.com/sagarredypatil/gradescope-ics, which also leverages the original Gradescope codebase from 
## Anton Pozharski, https://github.com/apozharski/gradescope-api.
##
## All original license terms apply.
##
## Modifications by Zack Ives, 2023+.
##
## Forms the crawler component for a broader Penn CIS Teaching Dashboard, https://github.com/upenn/gradescope-canvas-dashboard.
## The dashboard component is licensed under the Apache 2.0 license.
##
## Usage:
##  * Update config.yaml (copied from config.yaml.default) to include a Gradescope user ID and password.
##  * In Canvas, go to Settings, User Settings and add a New Access Token.  Copy the API key into config.yaml
##  * Copy the course IDs of any Canvas courses you'd like to add
##
#####################################################################################################################

import yaml
import sys, traceback
# import sqlite3
import pandas as pd
# import sqlalchemy
# from sqlalchemy.sql import text
from datetime import datetime
import duckdb

include_gradescope_data = True
include_canvas_data = True

with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)

    if 'show' in config['canvas']:
        include_canvas_data = config['canvas']['show']
        print ('Canvas data: {}'.format(include_canvas_data))

    if 'show' in config['gradescope']:
        include_gradescope_data = config['gradescope']['show']
        print ('Gradescope data: {}'.format(include_gradescope_data))


if 'db' in config:
    db_file = config['db']
else:
    db_file = 'dashboard.db'
#dbEngine=sqlalchemy.create_engine('sqlite:///./{}'.format(db_file)) # ensure this is the correct path for the sqlite file. 
dbEngine = duckdb.connect(db_file)

connection = dbEngine#.connect()

