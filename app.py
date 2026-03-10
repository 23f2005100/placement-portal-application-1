from flask import Flask
from application.database import db
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "placement-secret"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.app_context().push()

    with app.app_context():
        from application.models import User
        db.create_all()

        if User.query.filter_by(role="admin").first() is None:
            admin = User(
                email="admin@placement.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    return app

app = create_app()
from application.controllers import *

if __name__ == '__main__':
    app.run(debug=True)