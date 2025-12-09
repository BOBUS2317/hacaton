from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rf_id = db.Column(db.Integer, nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    balance = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<User rf_id={self.rf_id}, balance={self.balance}>"

def get_password_by_rf_id(rf_id: int) -> str | None:
    user = User.query.filter_by(rf_id=rf_id).first()
    return user.password if user else None

def get_balance_by_rf_id(rf_id: int) -> int | None:
    user = User.query.filter_by(rf_id=rf_id).first()
    return user.balance if user else None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

