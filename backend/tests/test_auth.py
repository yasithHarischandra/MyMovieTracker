import pytest
from app.core.security import hash_password
from app.models.user import User

pytestmark = pytest.mark.asyncio

async def test_login_success(client, db_session):
    # Ensure user exists with a known valid password hash structure
    user = User(username="loginuser", hashed_password=hash_password("correcthorse"))
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/auth/token",
        data={"username": "loginuser", "password": "correcthorse"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_login_wrong_password(client, db_session):
    user = User(username="loginuser", hashed_password=hash_password("correcthorse"))
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/auth/token",
        data={"username": "loginuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

async def test_get_me_protected(auth_client, mock_user):
    # This automatically uses the auth_client override 
    response = await auth_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == mock_user.username
