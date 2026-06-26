import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///bugbounty_lab.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
