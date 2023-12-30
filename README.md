# Gradescope-Canvas Dashboard

![Logo](https://www.seas.upenn.edu/wp-content/uploads/2017/08/penn_logo.png)

Welcome to the Penn [Computer and Information Science Department](https://www.cis.upenn.edu/) Teaching Dashboard!  This project develops a *data dashboard* and grading platform for courses that combine Canvas and Gradescope components.  It has two roles:

* Continuous monitoring of student progress (including missed deadlines and low scores).
* Grade assessment across different components.

Our goal is a single aggregation point for tracking student progress (and triggering alarms as appropriate) across many courses.  Ultimately there will be both "pull" and "push" components (messages vs dashboard).

![Dashboard](dashboard-screenshot.png)

We pull from both the Gradescope and Canvas APIs.  This has required substantial development to find and leverage the "hooks" between the two systems.  In addition, various mechanisms have been implemented to allow the grades in one system (e.g., Gradescope) override the (potentially partly synced) grades in the other system.

## Getting Started

This library requires a bit of setup to ensure it crawls Gradescope and Canvas appropriately.

1. Copy `config.yaml.default` to `config.yaml`
1. Log into Canvas, go into Account, Settings, and create a **New Access Token** (give it a name like "Canvas Monitoring") and copy the key.
1. Update the `config.yaml` as follows:
* Change the YAML key `gradescope` / `gs_login` to the Gradescope email address of an account given instructor permission on the courses you want to monitor.
* Update `gradescope` / `gs_pwd` to the password for above account.
* Update `canvas` / `api_key` to the new Canvas access token you created above.
* Set `site` to your Canvas host URL (e.g., `https://canvas.upenn.edu` for Penn)

Optionally you'll want to restrict the courses to a subset of the available ones:
* `canvas` / `course_ids`: a list of specific Canvas course IDs to crawl, rather than all that are currently active.  Each should be on a separate line indented with a leading dash
* `gradescope` / `semesters`: a list of the Gradescope "years" / semesters to crawl

Depending on whether you use Gradescope, Canvas, or both for your course, you can also enable or disable Gradescope or Canvas crawling (`enabled` key in each section of the YAML file) or display (`show` key in each section).

Then set up and run the environment:

```bash
python -m venv venv # Create a virtual environment
chmod +x venv/bin/activate # Make the activate script executable
source venv/bin/activate # Activate the virtual environment
pip install -r requirements.txt # Install dependencies
python collect_events.py # Run the script
```

After the script runs, there should be a series of files in the `data` directory:
* `gs_courses.csv` / `canvas_courses.csv`: list of courses to which we have access
* `gs_assignments.csv` / `canvas_assignments.csv`: list of student assignments (quizzes, exams, HWs)
* `gs_students.csv` / `canvas_students.csv`: list of enrolled students by course_id
* `gs_extensions.csv` / `canvas_student_summaries.csv`: list of student info including late days, extensions, etc.
* `gs_submissions.csv` / `canvas_submissions.csv`: list of homework submissions including timestamps, whether late, etc.

However, the Data Dashboard now operates out of a SQLite3 database instance, in the form of the file `dashboard.py`.

## Rubrics

To get a birds-eye view of progress, you may want to set up a *grading rubric* in your `config.yaml` file.  Towards the end of the sample file you should see something like this:

```
rubric:
  1234:
    midterm1:
      substring: Midterm 1
      points: 15
      max_score: 80
      max_extra_credit: 0
      source: Gradescope
    quizzes:
      substring: review
      points: 7
      max_score: 210
      max_extra_credit: 0
      source: Canvas
```

The first key (`1234`) represents the *Canvas SIS Number* for your course.  You can easily get this by logging into your course Canvas site and looking at the number at the end of the URL.

Next we have a series of blocks representing different rubric components.  You can name each key as you prefer; each will show up as a score component table and as a column in the student scores.  There are several important keys to specify:

* `substring`.  The Dashboard will collect every Assignment in Gradescope and in Canvas.  Anything which has a name matching the `substring` will be considered part of this rubric item.

* `source` (optional).  Sometimes Canvas and Gradescope will be partly synced. You can limit your rubric item to only consider `Canvas` entries or only consider `Gradescope` entries. By default it considers any source.

* `points`. How many points in your final rubric (e.g., percentage points) is this item worth?

* `max_score` (optional). Sometimes you will allow for extra credit or other items.  The `max_score` represents the baseline for 100% credit. Default: the maximum score comes from the Gradescope or Canvas entry.

* `max_extra_credit` (optional). If students are allowed to exceed the `max_score`, do we threshold the extra credit? Default: no threshold.

## Running the Dashboard

On a daily basis, you should run the crawler tool to generate a fresh version of your course data (perhaps through `chron`):

```
python collect_events.py
```

To see the dashboard, run:

```
streamlit run dashboard.py
```


## Potential To-Dos:
* Add support for external CSVs, e.g., for participation.
* Add auto late penalties in the system.
* Add download from Gradescope Review Similarity for each assignment?
* Generate ics for all deadlines?

## Gradescope APIs

We leverage and adapt the `pyscope` API, which we have updated to 2023 Gradescope with extensions.  Gradescope does not really have an external API, but through some clever work by prior authors, HTML crawling is used to pull the important data and wrap it in objects.  Substantial additional work was done to link every Gradescope student to their underlying SIS user ID.

**Credit**: The original `pyscope` codebase is derived from Sagar Reddy Patil's Gradescope iCalendar Converter, [sagarredypatil/gradescope-ics](https://github.com/sagarredypatil/gradescope-ics). In turn this leverages a Gradescope extraction codebase from Anton Pozharski, [apozharski/gradescope-api](https://github.com/apozharski/gradescope-api).  This overall package inherits the AGPL license as a result of this.

However, new subsystems developed as part of this project use the standard Apache 2 license.

**Major changes**:
* Support for extracting courses for which we have either *instructor* or *student* access.  Instructor access has more comprehensive support, e.g., of downloading rosters.
* Instructor access uses the full **assignments** page rather than the main dashboard, for comprehensiveness.  This requires changes to parsing.
* New `course.get_roster()` API call.
* Roster extraction update to match the 2023 HTML formatting of Gradescope.
* Crawl roster settings to get student SIS IDs.
* Homework assignment extraction now pulls the assignment ID.
* Extraction of homework submissions.
* Extraction of homework extensions.

## Canvas APIs

We leverage the Canvas LTI APIs from the U of Florida library.  Substantial layering over these libraries has been added in the `pycanvas` package, and a common API between the Canvas and Gradescope modules has been implemented as `CourseApi`.

