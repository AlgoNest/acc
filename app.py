from flask import Flask, render_template, request, redirect, url_for, session, flash
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import check_password_hash
from datetime import datetime
from github_store import read_data, write_data
from whatsapp import send_message
import os, uuid
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if check_password_hash(os.getenv("ADMIN_PASSWORD_HASH"), password):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Incorrect password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    data, _ = read_data()
    return render_template("dashboard.html", students=data.get("students", []))

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        student = {
            "id": str(uuid.uuid4())[:8],
            "name": request.form.get("name"),
            "parent_phone": request.form.get("parent_phone"),
            "fee_amount": request.form.get("fee_amount"),
            "fee_due_day": int(request.form.get("fee_due_day"))
        }
        data, sha = read_data()
        data["students"].append(student)
        write_data(data, sha)
        flash("Student added successfully")
        return redirect(url_for("dashboard"))
    return render_template("add_student.html")

@app.route("/delete/<student_id>")
@login_required
def delete_student(student_id):
    data, sha = read_data()
    data["students"] = [s for s in data["students"] if s["id"] != student_id]
    write_data(data, sha)
    flash("Student removed")
    return redirect(url_for("dashboard"))

def send_fee_reminders():
    today = datetime.now().day
    data, sha = read_data()
    students = data.get("students", [])
    logs = data.get("logs", {})
    month = datetime.now().strftime("%B_%Y")

    for student in students:
        if today != student.get("fee_due_day"):
            continue
        key = f"{student['parent_phone']}_{month}"
        if key in logs:
            continue
        message = (
            f"Assalam o Alaikum,\n\n"
            f"Dear Parent of {student['name']},\n"
            f"Fee of Rs. {student['fee_amount']} is due for "
            f"{datetime.now().strftime('%B %Y')}.\n"
            f"Please clear at your earliest.\n\nThank you."
        )
        success = send_message(student["parent_phone"], message)
        if success:
            logs[key] = {
                "sent_at": datetime.now().isoformat(),
                "student": student["name"],
                "amount": student["fee_amount"]
            }

    data["logs"] = logs
    write_data(data, sha)

scheduler = BackgroundScheduler()
scheduler.add_job(send_fee_reminders, "cron", hour=9, minute=0)
scheduler.start()

@app.route("/run-reminders")
@login_required
def test_run():
    send_fee_reminders()
    flash("Reminders sent — check WhatsApp")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=False)
