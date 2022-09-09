from flask import Flask, request, Response, render_template
from main import do_the_thing

app = Flask(__name__)


@app.route("/")
def index():
    # use tempelate index.html
    return render_template("index.html")


@app.route("/gradescope.ics")
def gradescope_ics():
    args = request.args
    email = args.get("email")
    pwd = args.get("pwd")

    semSeason = args.get("semSeason")
    semYear = args.get("semYear")

    sem = None

    if semSeason is not None and semYear is not None:
        sem = f"{semSeason} {semYear}"

    ical = "".join(
        do_the_thing(
            email,
            pwd,
            sem,
        )
    )

    return Response(ical, mimetype="text/calendar")
