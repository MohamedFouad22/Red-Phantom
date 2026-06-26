from flask import Flask

from .models import db


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object("lab.config.Config")

    db.init_app(app)

    with app.app_context():
        from .seed import seed_challenges

        db.create_all()
        seed_challenges()

    return app
