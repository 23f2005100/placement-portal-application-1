from .database import db
from datetime import datetime, timezone
<<<<<<< HEAD
from sqlalchemy import UniqueConstraint

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  
    is_blacklisted = db.Column(db.Boolean, default=False)

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    drives = db.relationship('Drive', backref='company', lazy=True)
    applications = db.relationship('Application', backref='company', lazy=True)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    education = db.Column(db.String(200))
    skills = db.Column(db.String(300))
    resume_filename = db.Column(db.String(200))
    applications = db.relationship('Application', backref='student', lazy=True)

class Drive(db.Model):
    __tablename__ = 'drive'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    drive_name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.String(300))
    salary = db.Column(db.String(100))
    deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    applications = db.relationship('Application', backref='drive', lazy=True)

class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    applied_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    status = db.Column(db.String(30), default="Applied")
    # Applied / Shortlisted / Selected / Rejected / Pending

    __table_args__ = (
        UniqueConstraint('student_id', 'drive_id', name='unique_application'),
    )
=======

class User(db.Model):
    __tablename__ = 'user'
    id             = db.Column(db.Integer, primary_key=True)
    email          = db.Column(db.String(100), unique=True, nullable=False)
    password       = db.Column(db.String(200), nullable=False)   # hashed
    role           = db.Column(db.String(20),  nullable=False)   # admin | doctor | patient
    is_blacklisted = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id':             self.id,
            'email':          self.email,
            'role':           self.role,
            'is_blacklisted': self.is_blacklisted,
        }

class Department(db.Model):
    __tablename__ = 'department'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    doctors     = db.relationship('Doctor', backref='department', lazy=True)

    def to_dict(self):
        return {
            'id':           self.id,
            'name':         self.name,
            'description':  self.description,
            'doctor_count': len(self.doctors),
        }

class Doctor(db.Model):
    __tablename__ = 'doctor'
    id            = db.Column(db.Integer, primary_key=True)
    fullname      = db.Column(db.String(100), nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    qualification = db.Column(db.String(200), nullable=False)
    description   = db.Column(db.Text, nullable=True)
    contact       = db.Column(db.String(20))
    experience    = db.Column(db.String(100), nullable=False)
    appointments  = db.relationship('Appointment', backref='doctor', lazy=True)
    availability  = db.relationship('Availability', backref='doctor', lazy=True)

    def to_dict(self):
        return {
            'id':              self.id,
            'fullname':        self.fullname,
            'user_id':         self.user_id,
            'department_id':   self.department_id,
            'department_name': self.department.name if self.department else None,
            'qualification':   self.qualification,
            'description':     self.description,
            'contact':         self.contact,
            'experience':      self.experience,
        }


class Patient(db.Model):
    __tablename__ = 'patient'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact      = db.Column(db.String(20))
    gender       = db.Column(db.String(10))
    age          = db.Column(db.Integer)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def to_dict(self):
        return {
            'id':      self.id,
            'name':    self.name,
            'user_id': self.user_id,
            'contact': self.contact,
            'gender':  self.gender,
            'age':     self.age,
        }

class Appointment(db.Model):
    __tablename__ = 'appointment'
    id         = db.Column(db.Integer, primary_key=True)
    doctor_id  = db.Column(db.Integer, db.ForeignKey('doctor.id'),  nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    time       = db.Column(db.Time, nullable=False)
    status     = db.Column(db.String(20), default='Booked')  # Booked | Completed | Cancelled
    treatment  = db.relationship('Treatment', backref='appointment', uselist=False)

    def to_dict(self):
        return {
            'id':           self.id,
            'doctor_id':    self.doctor_id,
            'doctor_name':  self.doctor.fullname if self.doctor else None,
            'department':   self.doctor.department.name if self.doctor and self.doctor.department else None,
            'patient_id':   self.patient_id,
            'patient_name': self.patient.name if self.patient else None,
            'date':         str(self.date),
            'time':         str(self.time),
            'status':       self.status,
            'treatment':    self.treatment.to_dict() if self.treatment else None,
        }

class Treatment(db.Model):
    __tablename__ = 'treatment'
    id             = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    visit_type     = db.Column(db.String(100))
    test_done      = db.Column(db.String(200))
    diagnosis      = db.Column(db.String(500))
    prescription   = db.Column(db.String(500))
    medicines      = db.Column(db.String(500))
    next_visit     = db.Column(db.String(100))
    notes          = db.Column(db.Text)
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':             self.id,
            'appointment_id': self.appointment_id,
            'visit_type':     self.visit_type,
            'test_done':      self.test_done,
            'diagnosis':      self.diagnosis,
            'prescription':   self.prescription,
            'medicines':      self.medicines,
            'next_visit':     self.next_visit,
            'notes':          self.notes,
            'created_at':     str(self.created_at),
        }

class Availability(db.Model):
    __tablename__ = 'availability'
    id           = db.Column(db.Integer, primary_key=True)
    doctor_id    = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date         = db.Column(db.Date, nullable=False)
    slot         = db.Column(db.String(100), nullable=False)   # e.g. "08:00-12:00"
    is_available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id':           self.id,
            'doctor_id':    self.doctor_id,
            'date':         str(self.date),
            'slot':         self.slot,
            'is_available': self.is_available,
        }
>>>>>>> 2c93572dacb45421110d8d8738251dfa4467252d
