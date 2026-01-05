import json
from threading import Thread

from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Response
from librouteros.query import Key
from sqlalchemy import text, select, func

from PropertyHelper import PropertyHelper
from models import db, Item, TestCase
import yaml
import os
from librouteros import connect
from librouteros.login import plain
from RunLogic import *
from TestData import *
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from flask import render_template, request, redirect, url_for, flash

scheduler = BackgroundScheduler()


app = Flask(__name__)
app.secret_key = "super-secret-key-change-me"

TESTCASE_TYPES = ["ping", "http", "https", "ssh", "rdp", "dns", "tcp", "udp", "remote"]

propertiesHelper = PropertyHelper()
app.runState = "idle"

# SQLite config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def test_runner_job():
    run_background(app, db, None)

if not scheduler.running:
    scheduler.start()
    scheduler.add_job(
        test_runner_job,
        CronTrigger.from_crontab(propertiesHelper.getProperty("runTestsCron")),
        id="my_job",
        replace_existing=True,
    )

with app.app_context():
    db.create_all()
    if propertiesHelper.getProperty("insertTestData"):
        testData = TestData()
        testData.initTestData(db)

def get_routeros_connection():

    return connect(
        host=propertiesHelper.getProperty("ros_address"),
        username=propertiesHelper.getProperty("ros_username"),
        password=propertiesHelper.getProperty("ros_password"),
        login_method=plain
    )

# -----------------
# HTML PAGES
# -----------------

@app.route("/")
def home():
    connection = db.engine.connect()
    res = connection.execute(text('select count(id) from test_case;'))

    statement = select(func.count()).select_from(TestCase)
    testCaseCount: int = db.session.execute(statement).scalar()

    statement = select(func.count()).select_from(TestResult)
    testResultCount: int = db.session.execute(statement).scalar()

    return render_template("home.html", testCaseCount = testCaseCount, testResultCount = testResultCount, runState = app.runState)

@app.route("/testResults")
def testResults():
    testResults = TestResult.query.all()
    #TODO: use an SQL join here
    for testResult in testResults:
        testcase = db.session.query(TestCase).filter(TestCase.id == testResult.testCaseId).one()
        testResult.name = testcase.name
        if bool(testResult.result):
            testResult.resultMsg = "[OK]"
        else:
            testResult.resultMsg = "[FAILED]"

    return render_template("testResult.html", testResults=testResults)

@app.route("/testcases")
def testcases():
    testcases = TestCase.query.all()
    return render_template("testcases.html", testcases=testcases)

@app.route("/testcases/export")
def export_testcases():
    testcases = TestCase.query.all()
    data = [tc.to_dict() for tc in testcases]

    return Response(
        json.dumps(data, indent=2),
        mimetype="application/json",
        headers={
            "Content-Disposition": "attachment; filename=testcases.json"
        }
    )

@app.route("/testcase/deleteAll", methods=["POST"])
def delete_all_testcases():
    connection = db.engine.connect()
    connection.execute(text('delete from test_case;'))
    connection.execute(text('delete from test_result;'))
    connection.commit()
    return redirect(url_for("testcases"))

@app.route("/testcases/import", methods=["POST"])
def import_testcases():
    file = request.files.get("file")
    if not file:
        flash("No file uploaded")
        return redirect(url_for("testcases"))

    try:
        data = json.load(file)
    except json.JSONDecodeError:
        flash("Invalid JSON file")
        return redirect(url_for("testcases"))

    TestCase.query.delete()

    for item in data:
        db.session.add(TestCase.from_dict(item))

    db.session.commit()
    flash("Test cases imported successfully")
    return redirect(url_for("testcases"))


def run_background(a, db, testcaseId):
    with a.app_context():
        #one run at a time
        if a.runState == "running":
            print("One run at a time.")
            return
        a.runState = "running"
        try:
            connection = db.engine.connect()
            connection.execute(text("delete from test_result;"))
            connection.commit()

            rosApi = get_routeros_connection()
            runLogic = RunLogic()
            runLogic.run(db, rosApi, testcaseId)
            connection.close()
        finally:
            a.runState = "idle"

@app.route("/run/<testcaseId>", methods=["POST"])
def runOne(testcaseId):
    if request.method == "POST":
        t = Thread(
            target=run_background,
            args=(app, db, testcaseId),
            daemon=True
        )
        t.start()
    return render_template(
        "home.html",
    )


@app.route("/run", methods=["GET", "POST"])
def runAll():
    if request.method == "POST":
        t = Thread(
            target=run_background,
            args=(app, db, None),
            daemon=True
        )
        t.start()

    return render_template(
        "run.html",
    )


@app.route("/routeros/identity")
def routeros_identity_page():
    try:
        api = get_routeros_connection()
        identity = list(api.path("system", "identity"))[0]
        api.close()

        properties = propertiesHelper.getAll();

        return render_template(
            "routeros_identity.html",
            identity=identity.get("name", "unknown"),
            properties=properties
        )

    except Exception as e:
        return render_template(
            "routeros_identity.html",
            error=str(e)
        )

def save_testcase_from_form(testcase, creating):
    testcase.name = request.form.get("name", "").strip()
    testcase.type = request.form.get("type")
    testcase.dstAddr = request.form.get("dstAddr", "").strip()

    testcase.srcAddr = request.form.get("srcAddr") or None
    testcase.srcVlan = request.form.get("srcVlan") or None
    testcase.dstPort = request.form.get("dstPort") or None
    testcase.gateway = request.form.get("gateway") or None
    testcase.passOnFailure = 1 if request.form.get("passOnFailure") else 0
    testcase.aux = request.form.get("aux") or None

    errors = []

    validator = TestCaseValidator()
    try:
        validator.validate(testcase)
    except TestCaseValidationError as e:
        print(f"Validation failed: {e}")
        errors.append(e)

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template(
            "testcase_form.html",
            testcase=testcase,
            types=TESTCASE_TYPES,
            creating=creating
        )

    if creating:
        db.session.add(testcase)

    db.session.commit()
    flash("Test case saved successfully.", "success")
    return redirect(url_for("edit_testcase", testcase_id=testcase.id))


@app.route("/testcase/new", methods=["GET", "POST"])
def create_testcase():
    testcase = TestCase()  # empty object

    if request.method == "POST":
        return save_testcase_from_form(testcase, creating=True)

    return render_template(
        "testcase_form.html",
        testcase=testcase,
        types=TESTCASE_TYPES,
        creating=True
    )

@app.route("/testcase/<int:testcase_id>/dup", methods=["POST"])
def duplicate_testcase(testcase_id):
    testcase = TestCase.query.get_or_404(testcase_id)
    dup = testcase.dup()
    db.session.add(dup)
    db.session.commit()
    return redirect(url_for("testcases"))

@app.route("/testcase/<int:testcase_id>/edit", methods=["GET", "POST"])
def edit_testcase(testcase_id):
    testcase = TestCase.query.get_or_404(testcase_id)

    if request.method == "POST":
        return save_testcase_from_form(testcase, creating=False)

    return render_template(
        "testcase_form.html",
        testcase=testcase,
        types=TESTCASE_TYPES,
        creating=False
    )

@app.route("/testcase/<int:testcase_id>/delete", methods=["POST"])
def delete_testcase(testcase_id):
    testcase = TestCase.query.get_or_404(testcase_id)

    if request.method == "POST":
        db.session.delete(testcase)
        db.session.commit()

    return redirect(url_for("testcases"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

    # -----------------
    # REST API
    # -----------------

    @app.route("/api/testcases", methods=["GET"])
    def api_get_testcases():
        testcases = TestCase.query.all()
        return jsonify([testcase.to_dict() for testcase in testcases])


    @app.route("/api/testcases", methods=["POST"])
    def api_add_testcase():
        data = request.get_json()
        TestCase.query.delete()

        validator = TestCaseValidator()

        for item in data:
            testcase = TestCase.from_dict(item)
            try:
                validator.validate(testcase)
                db.session.add(testcase)
            except TestCaseValidationError as e:
                print(f"Validation failed: {e}")

            db.session.add(testcase)
        db.session.commit()

        return "{}", 201

    @app.route("/api/result", methods=["GET"])
    def api_get_result():
        testResults = TestResult.query.all()
        return jsonify([testResult.to_dict() for testResult in testResults])