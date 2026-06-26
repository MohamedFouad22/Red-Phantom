from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    solves = db.relationship("Solve", back_populates="user", cascade="all, delete-orphan")

    @property
    def score(self):
        return sum(solve.challenge.points for solve in self.solves)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    objective = db.Column(db.Text, nullable=False)
    local_target = db.Column(db.Text, nullable=False)
    flag = db.Column(db.String(255), nullable=False)

    solves = db.relationship("Solve", back_populates="challenge", cascade="all, delete-orphan")


class Solve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"), nullable=False)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="solves")
    challenge = db.relationship("Challenge", back_populates="solves")

    __table_args__ = (db.UniqueConstraint("user_id", "challenge_id", name="uq_user_challenge"),)
