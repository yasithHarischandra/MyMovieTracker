import pytest

pytestmark = pytest.mark.asyncio

async def test_clear_history(auth_client):
    # 1. Add a show
    show_res = await auth_client.post("/api/shows", json={"tmdb_id": 456})
    show_id = show_res.json()["id"]
    
    # 2. Mark an episode as watched
    get_res = await auth_client.get(f"/api/shows/{show_id}")
    ep_id = get_res.json()["seasons"][0]["episodes"][0]["id"]
    await auth_client.post(f"/api/shows/{show_id}/episodes/{ep_id}/watch", json={'rating': 5})
    
    # 3. Add a movie and mark as watched
    movie_res = await auth_client.post("/api/movies", json={"tmdb_id": 100})
    movie_id = movie_res.json()["id"]
    await auth_client.post(f"/api/movies/{movie_id}/watch", json={'rating': 4})
    
    # Verify history is not empty
    hist_res = await auth_client.get("/api/history")
    assert len(hist_res.json()) == 2
    
    # 4. Clear history
    clear_res = await auth_client.delete("/api/history")
    assert clear_res.status_code == 204
    
    # 5. Verify history is empty
    hist_res_after = await auth_client.get("/api/history")
    assert len(hist_res_after.json()) == 0
    
    # Verify stats are reset
    dash_res = await auth_client.get("/api/dashboard")
    stats = dash_res.json()["stats"]
    assert stats["movies"]["movies_watched"] == 0
    assert stats["series"]["episodes_watched"] == 0
