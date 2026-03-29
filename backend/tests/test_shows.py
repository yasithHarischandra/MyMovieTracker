import pytest

pytestmark = pytest.mark.asyncio

async def test_add_show(auth_client):
    # tmdb_service.get_show_details returns a show + 1 season with 2 eps
    response = await auth_client.post("/api/shows", json={"tmdb_id": 456})
    assert response.status_code == 201
    
    # Check fully loaded tree returned by GET
    get_res = await auth_client.get(f"/api/shows/{response.json()['id']}")
    data = get_res.json()
    assert data["name"] == "Test Show"
    assert data["total_episodes"] == 2
    assert data["watched_episodes"] == 0
    assert data["remaining_episodes"] == 2

async def test_mark_episode_watched(auth_client):
    show_res = await auth_client.post("/api/shows", json={"tmdb_id": 456})
    show_id = show_res.json()["id"]
    
    get_res = await auth_client.get(f"/api/shows/{show_id}")
    ep_id = get_res.json()["seasons"][0]["episodes"][0]["id"]

    watch_res = await auth_client.post(f"/api/shows/{show_id}/episodes/{ep_id}/watch", json={'rating': 5})
    assert watch_res.status_code == 201

    # Check dashboard stats
    dash_res = await auth_client.get("/api/dashboard")
    stats = dash_res.json()["stats"]["series"]
    assert stats["episodes_watched"] == 1
    assert stats["in_progress_count"] == 1

async def test_mark_season_watched_completes_show(auth_client):
    show_res = await auth_client.post("/api/shows", json={"tmdb_id": 456})
    show_id = show_res.json()["id"]

    watch_res = await auth_client.post(f"/api/shows/{show_id}/seasons/1/watch")
    assert watch_res.status_code == 201
    assert watch_res.json()["marked_watched"] == 2  # Season has 2 episodes mocked

    get_res = await auth_client.get(f"/api/shows/{show_id}")
    data = get_res.json()
    assert data["watched_episodes"] == 2
    assert data["remaining_episodes"] == 0
    assert data["seasons"][0]["is_complete"] is True

    # Completed show should NOT be in in-progress
    prog_res = await auth_client.get("/api/shows/in-progress")
    assert len(prog_res.json()) == 0
