from models import User, db


def sign_in(client, password="test-password-long-enough"):
    token = client.get("/api/auth/csrf").json["csrf_token"]
    return client.post("/api/auth/login", headers={"X-CSRF-Token": token}, json={
        "email": "recruiter@example.invalid", "password": password,
    })


def test_cookie_login_logout(app):
    browser = app.test_client()
    assert browser.get("/api/auth/me").status_code == 401
    assert browser.get("/api/jobs").status_code == 401
    assert browser.post("/api/auth/login", json={"email": "x", "password": "x"}).status_code == 403
    assert sign_in(browser, "wrong-password").status_code == 401
    result = sign_in(browser)
    assert result.status_code == 200
    assert result.json["user"]["name"] == "Test Recruiter"
    cookie = result.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert "password" not in str(result.json)
    assert browser.post("/api/auth/logout").status_code == 403
    token = result.json["csrf_token"]
    old_cookie = browser.get_cookie("session").value
    assert browser.post("/api/auth/logout", headers={"X-CSRF-Token": token}).status_code == 200
    assert browser.get("/api/jobs").status_code == 401
    browser.set_cookie("session", old_cookie)
    assert browser.get("/api/jobs").status_code == 401


def test_mutation_requires_csrf(app, job_payload):
    browser = app.test_client()
    response = sign_in(browser)
    assert browser.post("/api/jobs", json=job_payload).status_code == 403
    assert browser.post("/api/jobs", json=job_payload, headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert browser.post("/api/jobs", json=job_payload, headers={"X-CSRF-Token": response.json["csrf_token"]}).status_code == 201


def test_password_is_hashed_and_membership_revoked(app, client):
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user.password_hash != "test-password-long-enough"
        assert user.check_password("test-password-long-enough")
        assert not user.check_password("incorrect")
        user.active = False
        db.session.commit()
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/jobs").status_code == 401
