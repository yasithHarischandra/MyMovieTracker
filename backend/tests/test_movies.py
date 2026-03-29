import pytest

pytestmark = pytest.mark.asyncio

async def test_add_movie_success(auth_client):
    # tmdb_service.get_movie_details is completely mocked in conftest.py
    response = await auth_client.post("/api/movies", json={"tmdb_id": 123})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Movie"
    assert data["tmdb_id"] == 123
    assert data["runtime_mins"] == 120

async def test_add_duplicate_movie(auth_client):
    # Add once
    await auth_client.post("/api/movies", json={"tmdb_id": 123})
    # Add again
    response = await auth_client.post("/api/movies", json={"tmdb_id": 123})
    assert response.status_code == 409
    assert "already in library" in response.json()["detail"]

async def test_mark_watched_and_history(auth_client):
    movie_res = await auth_client.post("/api/movies", json={"tmdb_id": 123})
    movie_id = movie_res.json()["id"]

    # Mark watched
    watch_res = await auth_client.post(f"/api/movies/{movie_id}/watch", json={"rating": 5, "note": "Great testing"})
    assert watch_res.status_code == 201
    watch_id = watch_res.json()["id"]
    assert watch_res.json()["rating"] == 5

    # Check history
    hist_res = await auth_client.get(f"/api/movies/{movie_id}/history")
    assert len(hist_res.json()) == 1
    assert hist_res.json()[0]["id"] == watch_id
    
    # Check global stats
    dash_res = await auth_client.get(f"/api/dashboard")
    stats = dash_res.json()["stats"]
    assert stats["movies"]["movies_watched"] == 1
    assert stats["movies"]["movie_hours_watched"] == 2.0  # 120 / 60

async def test_unwatch_movie(auth_client):
    movie_res = await auth_client.post("/api/movies", json={"tmdb_id": 123})
    movie_id = movie_res.json()["id"]

    watch_res = await auth_client.post(f"/api/movies/{movie_id}/watch", json={"rating": 5})
    watch_id = watch_res.json()["id"]

    # Delete watch
    delete_res = await auth_client.delete(f"/api/movies/watch/{watch_id}")
    assert delete_res.status_code == 204

    # Stats should be zero
    hist_res = await auth_client.get(f"/api/movies/{movie_id}/history")
    assert len(hist_res.json()) == 0
