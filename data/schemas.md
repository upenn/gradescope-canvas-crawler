# Schema Merging Notes

Merging records across the two systems is nontrivial.

We will only do this at the Dashboard level if `config.yaml` specifies we should look for data files from both systems:

* `canvas` key `show: true`
* `gradescope` key `show: true`

### Courses

Canvas and Gradescope both have internal course IDs, and the names are not always synced. However, we can use the SIS / LTI course ID as the basis of merging.

```
canvas_courses(id,name,start_at,end_at,workflow_state,is_public,sis_course_id)
gs_courses(cid,name,shortname,year,lti)
```

* Use `sis_course_id` from Canvas and `lti` from Gradescope

### Students

There is no 100% definitive way of joining students across Gradescope and Canvas: we assume the student ID is set (as SIS_user_id in Canvas, and either via sync or manually in Gradescope under the user settings).

```
gs_students(sid,student_id,name,emails,user_id,role,course_id)
canvas_students(id,name,sortable_name,login_id,email,sis_user_id,created_at,course_id)
```

* Need to map both `course_id`s to the SIS course ID.
* Use `student_id` in Gradescope as the student ID
* Use `sis_student_id` in Canvas as the student ID

### Assignments

```
canvas_assignments(id,name,due_at,unlock_at,lock_at,points_possible,allowed_attempts,muted,course_id)
gs_assignments(id,name,assigned,due,course_id)
```

* Need to map both `course_id`s to the SIS course ID.
* Need to union together complementary assignments and merge identical ones
    * Is there a mapping from GS assignment ID to/from Canvas course ID?

### Submissions

```
gs_submissions(First Name,Last Name,SID,Email,Sections,Total Score,Max Points,Status,Submission ID,Submission Time,Lateness (H:M:S),View Count,Submission Count, ...)
canvas_submissions(id,assignment_id,user_id,grade,submitted_at,graded_at,grader_id,score,excused,late_policy_status,points_deducted,late,missing,entered_grade,entered_score,course_id)
```

### Extensions

```
gs_extensions(First & Last Name Swap,"Last, First Name Swap",Extension Type,Sections,Release (EST),Due (EST),Late Due (EST),Time Limit,Edit,course_id,assign_id,user_id,Section,Release (EST)Due (EST))
```

## TODO

Allow for `config.yaml` to specify a set of *summary reports* and *detailed reports*.  For each course allow a *rubric*, a *sort priority*, a *partitioning*, and a *color map*.  Optionally create
an email button for members of each color?

Support outer union.  Allow outer union of different HW/module scores into one wide table (but also summary scores).

Track `last_active` (submission date?), num_unsubmitted, num_late.