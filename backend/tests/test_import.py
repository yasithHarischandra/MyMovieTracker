import pytest
import json

pytestmark = pytest.mark.asyncio

async def test_import_legacy_format(auth_client, mocker):
    mocker.patch("app.services.tmdb_service.get_movie_detail", return_value={
        "tmdb_id": 100, "title": "Test Movie", "overview": "Test.", "release_date": "2024-01-01",
        "runtime_mins": 120, "genres": "Action", "poster_path": "/test.jpg"
    })
    
    payload = {
        "movies": [
            {"movie": {"ids": {"tmdb": 100}}, "watched_at": "2024-01-01T00:00:00.000Z"}
        ],
        "episodes": []
    }
    
    files = {"file": ("test.json", json.dumps(payload).encode(), "application/json")}
    res = await auth_client.post("/api/admin/import/trakt", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_movies"] == 1
    assert data["imported_episodes"] == 0
    assert len(data["skipped"]) == 0

async def test_import_new_movie_array(auth_client, mocker):
    mocker.patch("app.services.tmdb_service.get_movie_detail", return_value={
        "tmdb_id": 101, "title": "Test Movie 101", "overview": "Test.", "release_date": "2024-01-01",
        "runtime_mins": 120, "genres": "Action", "poster_path": "/test.jpg"
    })
    
    payload = [
        {"movie": {"ids": {"tmdb": 101}, "title": "Test Movie 101"}, "last_watched_at": "2024-01-01T00:00:00.000Z"},
        {"movie": {"ids": {"imdb": "missing_tmdb"}, "title": "Bad Movie"}, "last_watched_at": "2024-01-01T00:00:00.000Z"}
    ]
    
    files = {"file": ("test.json", json.dumps(payload).encode(), "application/json")}
    res = await auth_client.post("/api/admin/import/trakt", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_movies"] == 1
    assert data["imported_episodes"] == 0
    assert len(data["skipped"]) == 1
    assert data["skipped"][0]["title"] == "Bad Movie"
    assert data["skipped"][0]["reason"] == "Missing TMDB ID"

async def test_import_new_show_array(auth_client, mocker):
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

    payload = [
        {
            "show": {"ids": {"tmdb": 456}, "title": "Test Show"},
            "seasons": [
                {
                    "number": 1,
                    "episodes": [
                        {"number": 1, "last_watched_at": "2024-01-01T00:00:00.000Z"},
                        {"number": 99, "last_watched_at": "2024-01-01T00:00:00.000Z"} # Will be skipped (mapping failed max ep is 2)
                    ]
                }
            ]
        }
    ]

    files = {"file": ("test.json", json.dumps(payload).encode(), "application/json")}
    res = await auth_client.post("/api/admin/import/trakt", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["imported_episodes"] == 1
    assert data["imported_movies"] == 0
    assert len(data["skipped"]) == 1
    assert data["skipped"][0]["title"] == "Test Show"
    assert "Mapping Failed" in data["skipped"][0]["reason"]
