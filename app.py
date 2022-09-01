from flask import Flask, request, make_response
from main import do_the_thing

app = Flask(__name__)


@app.route("/gradescope")
def gradescope_ics():
    args = request.args
    email = args.get("email")
    pwd = args.get("pwd")

    response = make_response("".join(do_the_thing(email, pwd)))
    response.headers["Content-Disposition"] = "attachment; filename=gradescope.ics"
    return response
