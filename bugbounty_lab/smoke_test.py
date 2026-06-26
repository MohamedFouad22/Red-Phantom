from app import app
from lab.models import Challenge, User, db


def run():
    with app.app_context():
        existing = User.query.filter_by(username="smoke_user").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        first_challenge = Challenge.query.order_by(Challenge.points.asc()).first()
        assert first_challenge is not None, "No challenges seeded."
        challenge_slug = first_challenge.slug
        challenge_flag = first_challenge.flag

    client = app.test_client()

    register_resp = client.post(
        "/register",
        data={"username": "smoke_user", "password": "smoke_pass_123"},
        follow_redirects=True,
    )
    assert register_resp.status_code == 200
    assert b"Registration successful" in register_resp.data

    login_resp = client.post(
        "/login",
        data={"username": "smoke_user", "password": "smoke_pass_123"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Welcome, smoke_user." in login_resp.data

    wrong_flag_resp = client.post(
        f"/challenge/{challenge_slug}/submit",
        data={"flag": "flag{wrong}"},
        follow_redirects=True,
    )
    assert wrong_flag_resp.status_code == 200
    assert b"Incorrect flag" in wrong_flag_resp.data

    correct_flag_resp = client.post(
        f"/challenge/{challenge_slug}/submit",
        data={"flag": challenge_flag},
        follow_redirects=True,
    )
    assert correct_flag_resp.status_code == 200
    assert b"Correct flag!" in correct_flag_resp.data

    scoreboard_resp = client.get("/scoreboard")
    assert scoreboard_resp.status_code == 200
    assert b"smoke_user" in scoreboard_resp.data

    print("Smoke test passed: register/login/submit/scoreboard flow works.")


if __name__ == "__main__":
    run()
