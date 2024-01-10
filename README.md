# Gradescope-Canvas Crawler

This project, developed at the Penn [Computer and Information Science Department](https://www.cis.upenn.edu/), pulls data
from Gradescope and Canvas for dashboard support.  It builds notably on two projects: (1) the Pyscope project by Anton Pozharskiy, (2) our own layering (called python_canvas_layer) to abstract the Canvas LMS APIs from U Florida.

## Getting Started

This library requires a bit of setup to ensure it crawls Gradescope and Canvas appropriately.

### Pre-configuration

Let's assume you have a course set up with both Canvas and Gradescope (though you don't need to utilize Canvas).

1. Log into Canvas, go into Account, Settings, and create a **New Access Token** (give it a name like "Canvas Monitoring") and copy the key.
1. Set up an email account for the Teaching Dashboard, e.g., via Outlook.com or GMail.  Add this account as an Instructor in your Gradescope course.

### Enabling Dashboard Access to Canvas and Gradescope

Copy `config.yaml.default` to `config.yaml`. Update the `config.yaml` as follows:
* Change the YAML key `gradescope` / `gs_login` to the Gradescope email address of an account given instructor permission on the courses you want to monitor.
* Update `gradescope` / `gs_pwd` to the password for above account.
* Update `canvas` / `api_key` to the new Canvas access token you created above.
* Set `site` to your Canvas host URL (e.g., `https://canvas.upenn.edu` for Penn)

Next you'll want to restrict the courses-crawled to a subset of the available ones:
* `canvas` key, `course_ids` list: a list of specific Canvas course IDs to crawl, rather than all that are currently active.  Each should be on a *separate line indented with a leading dash*.  **To get the Canvas ID, you just need to go to the Canvas course site and copy the numeric ID at the end of the URL.**
* `gradescope` / `semesters`: a list of the Gradescope "years" / semesters to crawl.  You can see these in Gradescope under **Your Courses**, e.g., "Fall 2023."

Depending on whether you use Gradescope, Canvas, or both for your course, you can also enable or disable crawling of the site (`enabled` key in each section of the YAML file) or display (`show` key in each section). *Caveat: the dashboard has been most extensively tested with integrated Canvas and Gradescope.*

### Setting up Your Python Environment

We assume Python 3.9 or higher.  Set up and run an Anaconda environment (you may need to substitute `python3` and `pip3` for `python` and `pip` below, depending on your setup):

```bash
python -m venv venv
chmod +x venv/bin/activate
source venv/bin/activate
pip install -r requirements.txt
```

Now you should be ready to do your first crawl!

### Crawling Data

Crawling is easy (but, fair warning -- Canvas throttles data fetching in a terrible way):

```bash
python collect_events.py
```

After the script runs, there should be a series of files in the `data` directory:
* `gs_courses.csv` / `canvas_courses.csv`: list of courses to which we have access
* `gs_assignments.csv` / `canvas_assignments.csv`: list of student assignments (quizzes, exams, HWs)
* `gs_students.csv` / `canvas_students.csv`: list of enrolled students by course_id
* `gs_extensions.csv` / `canvas_student_summaries.csv`: list of student info including late days, extensions, etc.
* `gs_submissions.csv` / `canvas_submissions.csv`: list of homework submissions including timestamps, whether late, etc.

In addition, the Teaching Dashboard creates a SQLite3 database instance, in the form of the file `dashboard.db` (overridable in `config.yaml` via the `db` key).  Tools such as the Penn CIS Teaching Dashboard (https://github.com/upenn/teaching-dashboard) make use of this database.

Each time you re-run the crawler, it will overwrite the existing data.

**TODO: in a future release, we will *only crawl Canvas submissions updated after the last-changed date*.**

### Seeing/updating the data manually
You should be able to run `sqlite3` followed by `.open dashboard.db` to access the database.  `.tables` will show all tables, `.schema {tablename}` will show the schema, `select * from {tablename}` will show contents. Use `.quit` to exit.

## Details/Credits on Gradescope "APIs"

We leverage and adapt the `pyscope` API, which we have updated to 2023 Gradescope with extensions.  Gradescope does not really have an external API, but through some clever work by prior authors, HTML crawling is used to pull the important data and wrap it in objects.  Substantial additional work was done to link every Gradescope student to their underlying SIS user ID.

**Credit**: The original `pyscope` codebase is derived from Sagar Reddy Patil's Gradescope iCalendar Converter, [sagarredypatil/gradescope-ics](https://github.com/sagarredypatil/gradescope-ics). In turn this leverages a Gradescope extraction codebase from Anton Pozharskiy, [apozharski/gradescope-api](https://github.com/apozharski/gradescope-api).  This overall package inherits the AGPL license as a result of this.

However, new subsystems developed as part of this project use the standard Apache 2 license.

**Major enhancements to gradescope-ics**:
* Support for extracting courses for which we have either *instructor* or *student* access.  Instructor access has more comprehensive support, e.g., of downloading rosters.
* Instructor access uses the full **assignments** page rather than the main dashboard, for comprehensiveness.  This requires changes to parsing.
* New `course.get_roster()` API call.
* Roster extraction update to match the 2023 HTML formatting of Gradescope.
* Crawl roster settings to get student SIS IDs.
* Homework assignment extraction now pulls the assignment ID.
* Extraction of homework submissions.
* Extraction of homework extensions.

## Details / Credits on the Canvas APIs

We leverage the Canvas LTI APIs from the U of Florida library.  Substantial layering over these libraries has been added in the `pycanvas` package, and a common API between the Canvas and Gradescope modules has been implemented as `CourseApi`.

