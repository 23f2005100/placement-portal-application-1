from flask import Flask, render_template,redirect,request,session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app as app
import os
from .models import *
from datetime import date

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        this_user = User.query.filter_by(email=email).first()

        if this_user:
          if this_user.is_blacklisted:           # check blacklist first
            return render_template("blacklisted.html")
          if check_password_hash(this_user.password, password):
              if this_user.role == "admin":
                return redirect("/admin_dashboard")
              elif this_user.role == "student":
                return redirect(f"/student_dashboard/{this_user.id}")
              else:
                company = Company.query.filter_by(user_id=this_user.id).first()
                if not company.is_approved:
                    return "Company not approved by Admin yet."
                return redirect(f"/company_dashboard/{this_user.id}")         
          else:
             return render_template("invalid_password.html")
        else:
           return render_template("not_exist.html")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    role = request.form["role"] 
    email = request.form["email"]
    pwd = request.form["pwd"]
    user_email = User.query.filter_by(email=email).first()

    if user_email:
      return render_template("already_exists.html")
    hashed_pwd = generate_password_hash(pwd)
    user = User(email=email, password=hashed_pwd, role=role)
    db.session.add(user)
    db.session.flush()

    if role == "student":
        name = request.form["name"]
        student = Student(fullname=name, user_id=user.id)
        db.session.add(student)
        db.session.commit()
        return redirect(f"/student_dashboard/{user.id}")
    else:
        company_name = request.form["company_name"]
        company = Company(company_name=company_name, user_id=user.id, is_approved=False)
        db.session.add(company)
        db.session.commit()
        return render_template("company_pending_approval.html")  

  return render_template("register.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    q = request.args.get("q")

    if q:
        id_filter = Student.id == int(q) if q.isdigit() else False
        all_student = Student.query.filter(
            (Student.fullname.ilike(f"%{q}%")) | id_filter
        ).all()
        all_company = Company.query.filter(
            Company.company_name.ilike(f"%{q}%")
        ).all()
    else:
        all_student = Student.query.all()
        all_company = Company.query.all()

    ongoing_drives = Drive.query.filter_by(status="Approved").all()
    completed_drives = Drive.query.filter_by(status="Closed").all()
    pending_companies = Company.query.filter_by(is_approved=False).all()
    pending_drives = Drive.query.filter_by(status="Pending").all() 
    student_applications = Application.query.filter_by(status="Applied").all()
    total_drives = Drive.query.count(),
    blacklisted_ids = {u.id for u in User.query.filter_by(is_blacklisted=True).all()}

    return render_template(
        "admin_dash.html",
        all_student=all_student,
        all_company=all_company,
        ongoing_drives=ongoing_drives,
        completed_drives=completed_drives,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        student_applications=student_applications,
        total_drives=total_drives,
        blacklisted_ids=blacklisted_ids,
        query=q)

@app.route("/approve_company/<int:id>")
def approve_company(id):

    company = Company.query.get(id)
    company.is_approved = True
    db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/reject_company/<int:id>")
def reject_company(id):
    company = Company.query.get(id)
    company.is_approved = False  
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/blacklist_company/<int:user_id>")
def blacklist_company(user_id):
    user = User.query.get(user_id)
    user.is_blacklisted = True
    company = Company.query.filter_by(user_id=user_id).first()
    for drive in Drive.query.filter_by(company_id=company.id).all():
        drive.status = "Cancelled"

    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/blacklist_student/<int:user_id>")
def blacklist_student(user_id):

    user = User.query.get(user_id)
    user.is_blacklisted = True
    db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/unblacklist_student/<int:user_id>")
def unblacklist_student(user_id):
    user = User.query.get(user_id)
    user.is_blacklisted = False
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/unblacklist_company/<int:user_id>")
def unblacklist_company(user_id):
    user = User.query.get(user_id)
    user.is_blacklisted = False
    db.session.commit()
    return redirect("/admin_dashboard")

@app.route("/approve_drive/<int:id>")
def approve_drive(id):

    drive = Drive.query.get(id)
    drive.status = "Approved"
    db.session.commit()

    return redirect("/admin_dashboard")

@app.route("/reject_drive/<int:id>")
def reject_drive(id):

    drive = Drive.query.get(id)
    drive.status = "Cancelled"
    db.session.commit()

    return redirect("/admin_dashboard")
@app.route("/admin_view_company/<int:company_id>")
def admin_view_company(company_id):
    company = Company.query.get(company_id)
    drives = Drive.query.filter_by(company_id=company_id).all()
    return render_template("admin_view_company.html", company=company, drives=drives)

@app.route("/view_drive/<int:drive_id>")
def view_drive(drive_id):
    drive = Drive.query.get(drive_id)  # gets drive with ID 1 from database
    
    return render_template("admin_view_drive.html", drive=drive)

@app.route("/view_student/<int:id>")
def view_student(id):

    student = Student.query.get(id)

    return render_template("admin_view_student.html", student=student)

@app.route("/company_dashboard/<int:user_id>")
def company_dashboard(user_id):

    company = Company.query.filter_by(user_id=user_id).first()

    today = date.today()

    ongoing_drives = Drive.query.filter(
        Drive.company_id == company.id,
        Drive.status == "Approved",
        Drive.deadline >= today        # deadline not yet passed
    ).all()

    pending_drives = Drive.query.filter_by(company_id=company.id, status="Pending").all()
    closed_drives = Drive.query.filter_by(
        company_id=company.id,
        status="Closed"
    ).all()

    cancelled_drives = Drive.query.filter_by(
        company_id=company.id,
        status="Cancelled"
    ).all()

    return render_template(
        "company_dash.html",
        company=company,
        ongoing_drives=ongoing_drives,
        pending_drives=pending_drives,
        closed_drives=closed_drives,
        cancelled_drives=cancelled_drives
    )

@app.route("/create_drive/<int:user_id>", methods=["GET", "POST"])
def create_drive(user_id):

    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        name = request.form["name"]
        title = request.form["title"]
        description = request.form["description"]
        eligibility = request.form["eligibility"]
        salary = request.form["salary"]
        deadline = request.form["deadline"]

        drive = Drive(
            company_id=company.id,
            drive_name = name,
            job_title=title,
            job_description=description,
            eligibility=eligibility,
            salary=salary,
            deadline=datetime.strptime(deadline, "%Y-%m-%d").date(),
            status="Pending"
        )

        db.session.add(drive)
        db.session.commit()

        return redirect(f"/company_dashboard/{user_id}")

    return render_template("create_drive.html", company=company)

@app.route("/edit_drive/<int:drive_id>/<int:user_id>", methods=["GET", "POST"])
def edit_drive(drive_id, user_id):
    drive = Drive.query.get(drive_id)
    if request.method == "POST":
        drive.drive_name = request.form["name"]
        drive.job_title = request.form["title"]
        drive.job_description = request.form["description"]
        drive.eligibility = request.form["eligibility"]
        drive.deadline = datetime.strptime(request.form["deadline"], "%Y-%m-%d").date()
        db.session.commit()
        return redirect(f"/company_dashboard/{user_id}")
    return render_template("edit_drive.html", drive=drive, user_id=user_id)


@app.route("/delete_drive/<int:drive_id>/<int:user_id>")
def delete_drive(drive_id, user_id):
    drive = Drive.query.get(drive_id)
    db.session.delete(drive)
    db.session.commit()
    return redirect(f"/company_dashboard/{user_id}")

@app.route("/cancel_drive/<int:drive_id>")
def cancel_drive(drive_id):
    drive = Drive.query.get(drive_id)
    drive.status = "Cancelled"
    db.session.commit()
    return redirect(f"/company_dashboard/{drive.company.user_id}")

@app.route("/mark_complete/<int:drive_id>")
def mark_complete(drive_id):

    drive = Drive.query.get(drive_id)
    drive.status = "Closed"        #route to admin dashboard or company dashboard?
    db.session.commit()

    return redirect(f"/company_dashboard/{drive.company.user_id}")

@app.route("/view_applicants/<int:drive_id>")
def view_applicants(drive_id):

    drive = Drive.query.get(drive_id)
    applications = Application.query.filter_by(drive_id=drive_id).all()

    return render_template(
        "company_view_applicants.html",
        drive=drive,
        applications=applications
    )

@app.route("/company_view_student/<int:application_id>")
def company_view_student(application_id):
    application = Application.query.get(application_id)
    return render_template("company_view_student.html", application=application)

ALLOWED = ["Shortlisted", "Selected", "Rejected"]
@app.route("/update_application/<int:id>/<string:new_status>")
def update_application(id, new_status):
    application = Application.query.get(id)
    if new_status in ALLOWED:
        application.status = new_status
        db.session.commit()
    return redirect(f"/view_applicants/{application.drive_id}")

@app.route("/company_profile/<int:user_id>", methods=["GET", "POST"])
def company_profile(user_id):
    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        company.contact = request.form["contact"]
        company.website = request.form["website"]
        company.description = request.form["description"]
        db.session.commit()
        return redirect(f"/company_profile/{user_id}")

    drives = Drive.query.filter_by(company_id=company.id, status="Approved").all()
    return render_template("company_profile.html", company=company, drives=drives)

@app.route("/student_dashboard/<int:user_id>")
def student_dashboard(user_id):

    student = Student.query.filter_by(user_id=user_id).first()

    companies = Company.query.filter_by(is_approved=True).all()

    approved_drives = Drive.query.filter_by(status="Approved").all()

    applied_drives = Application.query.filter_by(
        student_id=student.id
    ).all()

    return render_template(
        "student_dash.html",
        student=student,
        companies=companies,
        approved_drives=approved_drives,
        applied_drives=applied_drives
    )

@app.route("/student_view_company/<int:company_id>/<int:user_id>")
def student_view_company(company_id, user_id):
    company = Company.query.get(company_id)
    drives = Drive.query.filter_by(company_id=company_id, status="Approved").all()

    return render_template(
        "student_view_company.html",
        company=company,
        drives=drives,
        user_id=user_id
    )


@app.route("/student_drive/<int:drive_id>/<int:user_id>")
def student_drive(drive_id, user_id):
    drive = Drive.query.get(drive_id)

    # check if already applied — to show correct button
    student = Student.query.filter_by(user_id=user_id).first()
    already_applied = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()

    return render_template(
        "student_drive.html",
        drive=drive,
        user_id=user_id,
        already_applied=already_applied
    )


@app.route("/apply_drive/<int:drive_id>/<int:user_id>")
def apply_drive(drive_id, user_id):
    student = Student.query.filter_by(user_id=user_id).first()
    drive = Drive.query.get(drive_id)

    existing = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()

    if not existing:
        application = Application(
            student_id=student.id,
            drive_id=drive_id,
            company_id=drive.company_id,
            status="Applied"
        )
        db.session.add(application)
        db.session.commit()

    return redirect(f"/student_dashboard/{user_id}")


@app.route("/student_history/<int:user_id>")
def student_history(user_id):
    student = Student.query.filter_by(user_id=user_id).first()
    applications = Application.query.filter_by(student_id=student.id).all()

    return render_template(
        "student_history.html",
        student=student,
        applications=applications
    )

import os

@app.route("/edit_profile/<int:user_id>", methods=["GET", "POST"])
def edit_profile(user_id):
    student = Student.query.filter_by(user_id=user_id).first()
    if request.method == "POST":
        student.fullname = request.form["name"]
        student.education = request.form["education"]
        student.skills = request.form["skills"]

        if "resume" in request.files:
            file = request.files["resume"]
            if file.filename != "":
                os.makedirs("static/resumes", exist_ok=True)  # ✅ creates folder if missing
                filename = f"resume_{student.id}.pdf"
                file.save(os.path.join("static/resumes", filename))
                student.resume_filename = filename

        db.session.commit()
        return redirect(f"/student_dashboard/{user_id}")
    return render_template("student_edit_profile.html", student=student)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")