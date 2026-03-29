import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import FastAPI

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Workaround for passlib + bcrypt >= 4.0
import bcrypt
if not hasattr(bcrypt, "__about__"):
    class AboutMock:
        __version__ = "4.0.1"
    bcrypt.__about__ = AboutMock()

from app.main import app
from app.database import Base
from app.core.dependencies import get_db, get_current_user
from app.models.user import User

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None # NullPool
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Provides a test client that overrides the get_db dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testServer") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def mock_user(db_session):
    """Creates a basic mock user strictly bound to the current test sesssion."""
    user = User(username="testuser", hashed_password="hashedpassword123")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def auth_client(client, mock_user):
    """Client authenticated with the mock user using DI override."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_tmdb(mocker):
    """Globally mocks tmdb_service so tests don't hit the real API."""
    mocker.patch("app.services.tmdb_service.search_movies", return_value=[])
    mocker.patch("app.services.tmdb_service.search_shows", return_value=[])
    mocker.patch("app.services.tmdb_service.get_movie_detail", return_value={
        "tmdb_id": 123, "title": "Test Movie", "overview": "Test.", "release_date": "2024-01-01",
        "runtime_mins": 120, "genres": "Action", "poster_path": "/test.jpg"
    })
    mocker.patch("app.services.tmdb_service.get_show_detail", return_value={
        "tmdb_id": 456, "name": "Test Show", "overview": "Test.", "first_air_date": "2024-01-01",
        "genres": "Drama", "status": "Returning Series", "poster_path": "/test.jpg",
        "seasons": [{
            "season_number": 1, 
            "episode_count": 2, 
            "name": "Season 1", 
            "air_date": "2024-01-01",
            "episodes": [
                {"episode_number": 1, "name": "Ep 1", "runtime_mins": 45, "air_date": "2024-01-01"},
                {"episode_number": 2, "name": "Ep 2", "runtime_mins": 45, "air_date": "2024-01-08"}
            ]
        }]
    })
