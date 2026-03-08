from flask import request, jsonify, current_app as app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from application.models import User, Patient
from application.database import db


@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid password"}), 401
    if user.is_blacklisted:
        return jsonify({"error": "Account suspended. Contact admin."}), 403

    # get profile_id so Vue knows which dashboard data to fetch
    profile_id = None
    name       = None
    if user.role == "patient":
        p          = Patient.query.filter_by(user_id=user.id).first()
        profile_id = p.id   if p else None
        name       = p.name if p else None
    elif user.role == "doctor":
        from application.models import Doctor
        d          = Doctor.query.filter_by(user_id=user.id).first()
        profile_id = d.id       if d else None
        name       = d.fullname if d else None
    elif user.role == "admin":
        name = "Admin"

    token = create_access_token(identity={"user_id": user.id, "role": user.role})
    return jsonify({"token": token, "role": user.role,
                    "user_id": user.id, "profile_id": profile_id, "name": name}), 200


@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json()
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=email, password=generate_password_hash(password), role="patient")
    db.session.add(user)
    db.session.commit()

    patient = Patient(name=name, user_id=user.id)
    db.session.add(patient)
    db.session.commit()

    token = create_access_token(identity={"user_id": user.id, "role": "patient"})
    return jsonify({"token": token, "role": "patient",
                    "user_id": user.id, "profile_id": patient.id, "name": name}), 201


@app.route("/api/me", methods=["GET"])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user     = User.query.get(identity["user_id"])
    return jsonify(user.to_dict()) if user else (jsonify({"error": "Not found"}), 404)