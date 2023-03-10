# Gradescope-Canvas Dashboard

The [Computer and Information Science Department at Penn](https://www.cis.upenn.edu/) is building cross-departmental monitoring tools to help with advising and student support.

Our goal is a single aggregation point for tracking student progress (and triggering alarms as appropriate) across many courses.  Ultimately there will be both "pull" and "push" components (messages vs dashboard).

We pull from both the Gradescope and Canvas APIs.

## Gradescope APIs

We leverage and adapt the `pyscope` API, which we have updated to 2023 Gradescope with extensions.  Gradescope does not really have an external API, but through some clever work by prior authors, HTML crawling is used to pull the important data and wrap it in objects.

**Credit**: This version is derived from Sagar Reddy Patil's Gradescope iCalendar Converter, [sagarredypatil/gradescope-ics](https://github.com/sagarredypatil/gradescope-ics), which also leverages the original Gradescope codebase from Anton Pozharski, [apozharski/gradescope-api](https://github.com/apozharski/gradescope-api).

**Major changes**:
* Support for extracting courses for which we have either *instructor* or *student* access.  Instructor access has more comprehensive support, e.g., of downloading rosters.
* Instructor access uses the full **assignments** page rather than the main dashboard, for comprehensiveness.  This requires changes to parsing.
* New `course.get_roster()` API call.
* Roster extraction required updates to match the 2023 HTML formatting.

**To-Dos**:
* Add assignment Download CSV: `gradescope.com/courses/{number}/gradebook.csv`
* Add download from Review Similarity for each assignment?
* Download Extensions?

## Canvas APIs

We leverage the Canvas LTI APIs.

## Initial Usage

You'll need to first set your Gradescope login info in `config.yaml`, which should be copied from `config.yaml.default`. Then:

```bash
python -m venv venv # Create a virtual environment
chmod +x venv/bin/activate # Make the activate script executable
source venv/bin/activate # Activate the virtual environment
pip install -r requirements.txt # Install dependencies
python collect_events.py # Run the script
```

After the script runs, there should be a file called `gradescope.ics` in the current directory.

## Flask App

There's also a Flask app that can be called like this:
`http://0.0.0.0:whatever/gradescope?email=<write email here>&pwd=<write password here>`
