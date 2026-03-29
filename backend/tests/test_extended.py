import pytest
import json
from app.models.user import User
from app.core.security import hash_password
from app.core.dependencies import get_current_user

pytestmark = pytest.mark.asyncio

async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

async def test_search_movies(auth_client, mocker):
    mocker.patch("app.services.tmdb_service.search_movies", return_value=[
        {"tmdb_id": 1, "title": "Movie 1", "overview": "Desc 1", "release_date": "2024-01-01", "poster_path": "/path1.jpg", "genres": []}
    ])
    response = await auth_client.get("/api/search/movies?q=test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Movie 1"
    assert data[0]["in_library"] is False

async def test_search_shows(auth_client, mocker):
    mocker.patch("app.services.tmdb_service.search_shows", return_value=[
        {"tmdb_id": 2, "name": "Show 1", "overview": "Desc 2", "first_air_date": "2024-01-01", "poster_path": "/path2.jpg", "genres": [], "status": None}
    ])
    response = await auth_client.get("/api/search/shows?q=test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Show 1"
    assert data[0]["in_library"] is False

async def test_movie_detail(auth_client):
    # Add movie first
    add_res = await auth_client.post("/api/movies", json={"tmdb_id": 123})
    movie_id = add_res.json()["id"]
    
    # Get detail
    response = await auth_client.get(f"/api/movies/{movie_id}")
    assert response.status_code == 200
    assert response.json()["tmdb_id"] == 123
    assert response.json()["title"] == "Test Movie"

async def test_unmark_episode_watched(auth_client):
    show_res = await auth_client.post("/api/shows", json={"tmdb_id": 456})
    show_id = show_res.json()["id"]
    
    get_res = await auth_client.get(f"/api/shows/{show_id}")
    ep_id = get_res.json()["seasons"][0]["episodes"][0]["id"]

    # Mark watched (need json body)
    await auth_client.post(f"/api/shows/{show_id}/episodes/{ep_id}/watch", json={})
    
    # Check stats
    dash_res = await auth_client.get("/api/dashboard")
    assert dash_res.json()["stats"]["series"]["episodes_watched"] == 1
    
    # Unmark watched
    unwatch_res = await auth_client.delete(f"/api/shows/episodes/watch/{dash_res.json()['recent_activity'][0]['id']}") # Wait, the route is different in the code
    # In shows.py: @router.delete("/episodes/watch/{watch_history_id}")
    # BUT in docs it was DELETE /shows/{show_id}/episodes/{episode_id}/watch
    # AND in test_extended I wrote: await auth_client.delete(f"/api/shows/{show_id}/episodes/{ep_id}/watch")
    
    # Let's check shows.py again for the correct delete route.
    # @router.delete("/episodes/watch/{watch_history_id}")
    
    assert unwatch_res.status_code == 204
    
    # Check stats again
    dash_res = await auth_client.get("/api/dashboard")
    assert dash_res.json()["stats"]["series"]["episodes_watched"] == 0

async def test_history_and_stats(auth_client):
    # Add and watch movie
    movie_res = await auth_client.post("/api/movies", json={"tmdb_id": 123})
    movie_id = movie_res.json()["id"]
    await auth_client.post(f"/api/movies/{movie_id}/watch", json={})
    
    # Add and watch episode
    show_res = await auth_client.post("/api/shows", json={"tmdb_id": 456})
    show_id = show_res.json()["id"]
    get_res = await auth_client.get(f"/api/shows/{show_id}")
    ep_id = get_res.json()["seasons"][0]["episodes"][0]["id"]
    await auth_client.post(f"/api/shows/{show_id}/episodes/{ep_id}/watch", json={})
    
    # Get history
    hist_res = await auth_client.get("/api/history")
    data = hist_res.json()
    assert len(data) >= 2
    
    # Get history stats
    stats_res = await auth_client.get("/api/history/stats")
    assert stats_res.status_code == 200
    data = stats_res.json()
    assert data["movies_watched"] == 1
    assert data["episodes_watched"] == 1
    assert data["total_hours"] == 2.8 # (120/60) + round(45/60, 1) = 2.0 + 0.8

async def test_multi_tenant_isolation(client, db_session, mock_user):
    # Create another user
    user2 = User(username="user2", hashed_password="hashedpassword456")
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)
    
    # Authenticate as mock_user (user1)
    from app.main import app
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # User 1 adds a movie
    await client.post("/api/movies", json={"tmdb_id": 111})
    
    # Switch to User 2
    app.dependency_overrides[get_current_user] = lambda: user2
    
    # User 2 library should be empty
    dash_res = await client.get("/api/dashboard")
    assert dash_res.json()["stats"]["movies"]["movies_watched"] == 0
    
    app.dependency_overrides.clear()

async def test_admin_sync(auth_client, mocker):
    mocker.patch("app.services.sync_service.sync_returning_shows", return_value={"updated": 1})
    response = await auth_client.post("/api/admin/sync")
    assert response.status_code == 200
    assert response.json()["updated"] == 1

async def test_sync_only_returning_series(auth_client, db_session, mocker):
    # Add two shows: one Returning, one Ended
    mocker.patch("app.services.tmdb_service.get_show_detail", side_effect=[
        {"tmdb_id": 11, "name": "Returning", "status": "Returning Series", "seasons": []},
        {"tmdb_id": 22, "name": "Ended", "status": "Ended", "seasons": []}
    ])
    
    await auth_client.post("/api/shows", json={"tmdb_id": 11})
    await auth_client.post("/api/shows", json={"tmdb_id": 22})
    
    # Mock the sync_one_show function to track calls
    mock_sync_one = mocker.patch("app.services.sync_service._sync_one_show", return_value=None)
    
    from app.services.sync_service import sync_returning_shows
    await sync_returning_shows()
    
    # Only the returning show (id=1, since it's the first added in this test) should be synced
    # Wait, the ID might not be 1 depending on previous tests in the session.
    # But it should be exactly 1 call.
    assert mock_sync_one.call_count == 1
    # Check that the call was for the show with status "Returning Series"
    # We can fetch it from DB to be sure
    from app.models.tv_show import TvShow
    from sqlalchemy import select
    res = await db_session.execute(select(TvShow).where(TvShow.status == "Returning Series"))
    returning_show = res.scalar_one()
    mock_sync_one.assert_called_with(returning_show.id)

async def test_trakt_import(auth_client, mocker):
    trakt_data = {
        "movies": [
            {"movie": {"ids": {"tmdb": 123}}, "watched_at": "2024-01-01T10:00:00Z"}
        ],
        "episodes": [
            {"show": {"ids": {"tmdb": 456}}, "episode": {"season": 1, "number": 1}, "watched_at": "2024-01-01T11:00:00Z"}
        ]
    }
    
    files = {"file": ("trakt.json", json.dumps(trakt_data), "application/json")}
    response = await auth_client.post("/api/admin/import/trakt", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["imported_movies"] == 1
    assert data["imported_episodes"] == 1
    
    # Verify in dashboard
    dash_res = await auth_client.get("/api/dashboard")
    assert dash_res.json()["stats"]["movies"]["movies_watched"] == 1
    assert dash_res.json()["stats"]["series"]["episodes_watched"] == 1
