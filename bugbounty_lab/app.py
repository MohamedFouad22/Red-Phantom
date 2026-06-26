from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from lab import create_app
from lab.models import Challenge, Solve, User, db

app: Flask = create_app()


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.get("/")
def index():
    challenges = Challenge.query.order_by(Challenge.points.asc()).all()
    user = current_user()
    solved_ids = set()
    if user:
        solved_ids = {solve.challenge_id for solve in user.solves}
    category_counts = {}
    for challenge in challenges:
        category_counts[challenge.category] = category_counts.get(challenge.category, 0) + 1
    return render_template(
        "index.html",
        challenges=challenges,
        solved_ids=solved_ids,
        category_counts=sorted(category_counts.items(), key=lambda item: item[0]),
        total_points=sum(challenge.points for challenge in challenges),
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 6:
            flash("Username >= 3 chars and password >= 6 chars.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect(url_for("register"))

        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.", "ok")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        flash(f"Welcome, {user.username}.", "ok")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    flash("Logged out.", "ok")
    return redirect(url_for("index"))


@app.get("/challenge/<slug>")
@login_required
def challenge_details(slug):
    challenge = Challenge.query.filter_by(slug=slug).first_or_404()
    user = current_user()
    solved = bool(Solve.query.filter_by(user_id=user.id, challenge_id=challenge.id).first())
    return render_template("challenge.html", challenge=challenge, solved=solved)


@app.post("/challenge/<slug>/submit")
@login_required
def submit_flag(slug):
    challenge = Challenge.query.filter_by(slug=slug).first_or_404()
    user = current_user()

    existing = Solve.query.filter_by(user_id=user.id, challenge_id=challenge.id).first()
    if existing:
        flash("You already solved this challenge.", "ok")
        return redirect(url_for("challenge_details", slug=slug))

    submitted_flag = request.form.get("flag", "").strip()
    if submitted_flag == challenge.flag:
        solve = Solve(user_id=user.id, challenge_id=challenge.id)
        db.session.add(solve)
        db.session.commit()
        flash(f"Correct flag! +{challenge.points} points", "ok")
    else:
        flash("Incorrect flag, try again.", "error")

    return redirect(url_for("challenge_details", slug=slug))


@app.get("/scoreboard")
def scoreboard():
    users = User.query.all()
    ranking = sorted(users, key=lambda u: u.score, reverse=True)
    return render_template("scoreboard.html", ranking=ranking)


@app.get("/how-to-play")
def how_to_play():
    return render_template("how_to_play.html")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=7000)
