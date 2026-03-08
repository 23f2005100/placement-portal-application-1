from flask import request, jsonify, current_app as app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from application.database import db
from application.models import User, Doctor, Patient, Appointment, Department


# ── helper: check admin role ──
def admin_only():
    identity = get_jwt_identity()
    if identity["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403
    return None


@app.route("/api/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    err = admin_only()
    if err: return err

    return jsonify({
        "total_doctors":      Doctor.query.count(),
        "total_patients":     Patient.query.count(),
        "total_appointments": Appointment.query.count(),
    }), 200


@app.route("/api/admin/doctors", methods=["GET"])
@jwt_required()
def get_doctors():
    err = admin_only()
    if err: return err

    doctors = Doctor.query.join(User).filter(User.is_blacklisted == False).all()
    return jsonify([d.to_dict() for d in doctors]), 200


@app.route("/api/admin/doctors", methods=["POST"])
@jwt_required()
def add_doctor():
    err = admin_only()
    if err: return err

    data = request.get_json()
    required = ["fullname", "email", "password", "qualification", "experience", "department_id"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "All fields required"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 409

    user = User(email=data["email"],
                password=generate_password_hash(data["password"]),
                role="doctor")
    db.session.add(user)
    db.session.commit()

    doctor = Doctor(
        user_id=user.id,
        fullname=data["fullname"],
        qualification=data["qualification"],
        experience=data["experience"],
        description=data.get("description", ""),
        contact=data.get("contact", ""),
        department_id=data["department_id"]
    )
    db.session.add(doctor)
    db.session.commit()
    return jsonify(doctor.to_dict()), 201


@app.route("/api/admin/doctors/<int:doctor_id>", methods=["PUT"])
@jwt_required()
def update_doctor(doctor_id):
    err = admin_only()
    if err: return err

    doctor = Doctor.query.get_or_404(doctor_id)
    data   = request.get_json()

    doctor.fullname      = data.get("fullname",      doctor.fullname)
    doctor.qualification = data.get("qualification", doctor.qualification)
    doctor.experience    = data.get("experience",    doctor.experience)
    doctor.description   = data.get("description",   doctor.description)
    doctor.contact       = data.get("contact",       doctor.contact)
    doctor.department_id = data.get("department_id", doctor.department_id)
    db.session.commit()
    return jsonify(doctor.to_dict()), 200


@app.route("/api/admin/doctors/<int:doctor_id>", methods=["DELETE"])
@jwt_required()
def delete_doctor(doctor_id):
    err = admin_only()
    if err: return err

    doctor = Doctor.query.get_or_404(doctor_id)
    user   = User.query.get(doctor.user_id)
    db.session.delete(doctor)
    if user: db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Doctor deleted"}), 200


@app.route("/api/admin/doctors/<int:doctor_id>/blacklist", methods=["POST"])
@jwt_required()
def blacklist_doctor(doctor_id):
    err = admin_only()
    if err: return err

    doctor      = Doctor.query.get_or_404(doctor_id)
    user        = User.query.get(doctor.user_id)
    user.is_blacklisted = True
    # cancel all their booked appointments
    Appointment.query.filter_by(doctor_id=doctor_id, status="Booked").update({"status": "Cancelled"})
    db.session.commit()
    return jsonify({"message": "Doctor blacklisted"}), 200


@app.route("/api/admin/patients", methods=["GET"])
@jwt_required()
def get_patients():
    err = admin_only()
    if err: return err

    patients = Patient.query.join(User).filter(User.is_blacklisted == False).all()
    return jsonify([p.to_dict() for p in patients]), 200


@app.route("/api/admin/patients/<int:patient_id>", methods=["PUT"])
@jwt_required()
def update_patient(patient_id):
    err = admin_only()
    if err: return err

    patient = Patient.query.get_or_404(patient_id)
    data    = request.get_json()
    patient.name    = data.get("name",    patient.name)
    patient.contact = data.get("contact", patient.contact)
    patient.gender  = data.get("gender",  patient.gender)
    patient.age     = data.get("age",     patient.age)
    db.session.commit()
    return jsonify(patient.to_dict()), 200


@app.route("/api/admin/patients/<int:patient_id>/blacklist", methods=["POST"])
@jwt_required()
def blacklist_patient(patient_id):
    err = admin_only()
    if err: return err

    patient             = Patient.query.get_or_404(patient_id)
    user                = User.query.get(patient.user_id)
    user.is_blacklisted = True
    Appointment.query.filter_by(patient_id=patient_id, status="Booked").update({"status": "Cancelled"})
    db.session.commit()
    return jsonify({"message": "Patient blacklisted"}), 200


@app.route("/api/admin/appointments", methods=["GET"])
@jwt_required()
def get_all_appointments():
    err = admin_only()
    if err: return err

    status = request.args.get("status")  # optional filter
    query  = Appointment.query
    if status:
        query = query.filter_by(status=status)
    appointments = query.order_by(Appointment.date.desc()).all()
    return jsonify([a.to_dict() for a in appointments]), 200



@app.route("/api/admin/search", methods=["GET"])
@jwt_required()
def admin_search():
    err = admin_only()
    if err: return err

    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"doctors": [], "patients": []}), 200

    doctors = Doctor.query.join(Department).filter(
        db.or_(
            Doctor.fullname.ilike(f"%{q}%"),
            Department.name.ilike(f"%{q}%")
        )
    ).all()

    patients = Patient.query.filter(
        db.or_(
            Patient.name.ilike(f"%{q}%"),
            Patient.contact.ilike(f"%{q}%"),
            Patient.id == (int(q) if q.isdigit() else -1)
        )
    ).all()

    return jsonify({
        "doctors":  [d.to_dict() for d in doctors],
        "patients": [p.to_dict() for p in patients]
    }), 200



@app.route("/api/admin/departments", methods=["GET"])
@jwt_required()
def get_departments():
    err = admin_only()
    if err: return err

    return jsonify([d.to_dict() for d in Department.query.all()]), 200


@app.route("/api/admin/departments", methods=["POST"])
@jwt_required()
def add_department():
    err = admin_only()
    if err: return err

    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    if Department.query.filter_by(name=name).first():
        return jsonify({"error": "Department already exists"}), 409

    dept = Department(name=name, description=data.get("description", ""))
    db.session.add(dept)
    db.session.commit()
    return jsonify(dept.to_dict()), 201