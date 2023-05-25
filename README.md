# Gradescope-Canvas Dashboard

The [Computer and Information Science Department at Penn](https://www.cis.upenn.edu/) is building cross-departmental monitoring tools to help with advising and student support.

Our goal is a single aggregation point for tracking student progress (and triggering alarms as appropriate) across many courses.  Ultimately there will be both "pull" and "push" components (messages vs dashboard).

We pull from both the Gradescope and Canvas APIs.

## Gradescope APIs

We leverage and adapt the `pyscope` API, which we have updated to 2023 Gradescope with extensions.  Gradescope does not really have an external API, but through some clever work by prior authors, HTML crawling is used to pull the important data and wrap it in objects.

**Credit**: The Pyscope codebase is derived from Sagar Reddy Patil's Gradescope iCalendar Converter, [sagarredypatil/gradescope-ics](https://github.com/sagarredypatil/gradescope-ics), which also leverages the original Gradescope codebase from Anton Pozharski, [apozharski/gradescope-api](https://github.com/apozharski/gradescope-api).

**Major changes**:
* Support for extracting courses for which we have either *instructor* or *student* access.  Instructor access has more comprehensive support, e.g., of downloading rosters.
* Instructor access uses the full **assignments** page rather than the main dashboard, for comprehensiveness.  This requires changes to parsing.
* New `course.get_roster()` API call.
* Roster extraction required updates to match the 2023 HTML formatting.
* Standardized API with Canvas modules.

**To-Dos**:
* Add assignment Download CSV: `gradescope.com/courses/{number}/gradebook.csv`
* Add download from Review Similarity for each assignment?
* Download Extensions?

## Canvas APIs

We leverage the Canvas LTI APIs.  You will need to log into Canvas, go into Account, Settings, and create a **New Access Token** (give it a name like "Canvas Monitoring") and copy the key.

## Initial Usage

You'll need to first set some details in `config.yaml`, which should be initially copied from `config.yaml.default`:
* gradescope / `gs_login`: the Gradescope email address of an account given instructor permission on the courses you want to monitor
* gradescope / `gs_pwd`: password for above account
* `use_threads`: reserved for multithreaded crawl (currently inactive)
* canvas / `api_key`: access token as per description in "Canvas APIs" above
* `site`: URL to your Canvas host (e.g., `https://canvas.upenn.edu` for Penn)
* `course_ids`: a list of specific course IDs to crawl, rather than all that are currently active

Then set up and run the environment:

```bash
python -m venv venv # Create a virtual environment
chmod +x venv/bin/activate # Make the activate script executable
source venv/bin/activate # Activate the virtual environment
pip install -r requirements.txt # Install dependencies
python collect_events.py # Run the script
```

After the script runs, there should be a series of files in the current directory:
* gs_courses.csv / canvas_courses.csv: list of courses to which we have access
* gs_assignments.csv / canvas_assignments.csv: list of student assignments (quizzes, exams, HWs)
* gs_students.csv / canvas_students.csv: list of enrolled students by course_id
* canvas_student_summaries.csv: list of student summary info, including late days etc.
* gs_submissions.csv / canvas_submissions.csv: list of homework submissions including timestamps, whether late, etc.

## Flask App

There's also a Flask app that can be called like this:
`http://0.0.0.0:whatever/gradescope?email=<write email here>&pwd=<write password here>`
