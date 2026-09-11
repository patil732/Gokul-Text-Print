import os
import sys
import importlib.util
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

os.environ["PYTEST_CURRENT_TEST"] = "1"

spec = importlib.util.spec_from_file_location("app_entry", os.path.join(_ROOT, "app.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def test_auth_full_lifecycle():
    app = m.create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Test Login with all 4 RBAC roles
    roles = [
        ("Admin", "admin", "admin123"),
        ("CEO", "ceo", "ceo123"),
        ("Manager", "manager", "manager123"),
        ("Employee", "employee", "employee123"),
    ]
    for role, user, pwd in roles:
        res = client.post("/api/auth/login", json={"username": user, "password": pwd})
        assert res.status_code == 200, f"Login failed for {user}: {res.data}"
        data = res.get_json()
        assert data["success"] is True
        assert data["user"]["role"] == role
        print(f"PASS: Login for {user} ({role})")

    # 2. Test /api/auth/me for last logged in user (employee)
    res = client.get("/api/auth/me")
    assert res.status_code == 200
    me_data = res.get_json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["role"] == "Employee"
    print("PASS: /api/auth/me verified")

    # 3. Test Forgot Password
    res = client.post("/api/auth/forgot-password", json={"username": "employee"})
    assert res.status_code == 200
    token = res.get_json()["reset_token"]
    assert token is not None
    print("PASS: Forgot password generated token")

    # 4. Test Verify Token
    res = client.get(f"/api/auth/verify-reset-token?token={token}")
    assert res.status_code == 200
    assert res.get_json()["valid"] is True
    print("PASS: Verify reset token passed")

    # 5. Test Reset Password
    res = client.post("/api/auth/reset-password", json={"token": token, "password": "newemployeepassword123"})
    assert res.status_code == 200
    print("PASS: Reset password succeeded")

    # 6. Test Login with new password
    res = client.post("/api/auth/login", json={"username": "employee", "password": "newemployeepassword123"})
    assert res.status_code == 200
    print("PASS: Login with new password succeeded")

    # 7. Test Profile Update
    res = client.put("/api/auth/profile", json={"email": "updated_employee@gokultextprint.internal"})
    assert res.status_code == 200
    assert res.get_json()["user"]["email"] == "updated_employee@gokultextprint.internal"
    print("PASS: Profile update succeeded")

    # 8. Test Logout
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    print("PASS: Logout verified")

if __name__ == "__main__":
    test_auth_full_lifecycle()
    print("ALL TESTS PASSED SUCCESSFULLY!")
