# API Reference

> **Base URL:** `http://<host>/api`  
> **Authentication:** All endpoints (except `/auth/token`) require `Authorization: Bearer <token>` header.  
> **Interactive docs:** `/api/docs` (Swagger UI) | `/api/redoc` (ReDoc)

---

## Authentication

### `POST /auth/token`
Login and obtain a JWT.

**Request** (form-encoded):
```
username=admin&password=yourpassword
```

**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Response `401`:** Invalid credentials.

---

### `GET /auth/me`
Returns the currently authenticated user.

**Response `200`:**
```json
{
  "id": 1,
  "username": "admin"
}
```

---

## Search

### `GET /search/movies?q={query}`
Search TMDB for movies.

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query (min 1 char) |

**Response `200`:** Array of `MovieSearchResult`
```json
[
  {
    "tmdb_id": 550,
    "title": "Fight Club",
    "overview": "...",
    "release_date": "1999-10-15",
    "poster_path": "https://image.tmdb.org/t/p/w500/...",
    "in_library": false
  }
]
```

---

### `GET /search/shows?q={query}`
Search TMDB for TV shows.

**Response `200`:** Array of `ShowSearchResult`

---

## Movies

### `POST /movies`
Add a movie to your library (fetches metadata from TMDB).

**Body:**
```json
{ "tmdb_id": 550 }
```

**Response `201`:** `MovieBase` object  
**Response `409`:** Movie already in library  
**Response `502`:** TMDB fetch failed

---

### `GET /movies/{movie_id}`
Get details for a single movie.

**Response `200`:** `MovieBase`
```json
{
  "id": 1,
  "tmdb_id": 550,
  "title": "Fight Club",
  "overview": "...",
  "release_date": "1999-10-15",
  "runtime_mins": 139,
  "genres": "Drama,Thriller",
  "poster_path": "https://...",
  "added_at": "2024-01-01T00:00:00Z"
}
```

---

### `POST /movies/{movie_id}/watch`
Log a watch entry for a movie.

**Body:**
```json
{
  "rating": 5,
  "note": "Masterpiece"
}
```
*(Both fields optional; `rating` is 1–5)*

**Response `201`:** `WatchHistoryEntry`

---

### `GET /movies/{movie_id}/history`
Get all watch entries for a movie.

**Response `200`:** Array of `WatchHistoryEntry`

---

### `DELETE /movies/watch/{watch_history_id}`
Remove a watch history entry.

**Response `204`:** No content  
**Response `404`:** Entry not found

---

## TV Shows

### `POST /shows`
Add a TV show to your library.

**Body:**
```json
{ "tmdb_id": 1396 }
```

**Response `201`:** Show summary object  
**Response `409`:** Show already in library

---

### `GET /shows/{show_id}`
Get full show details with seasons, episodes, and per-episode watched status.

**Response `200`:**
```json
{
  "id": 1,
  "tmdb_id": 1396,
  "name": "Breaking Bad",
  "overview": "...",
  "status": "Ended",
  "poster_path": "https://...",
  "total_episodes": 62,
  "watched_episodes": 30,
  "remaining_episodes": 32,
  "remaining_hours": 24.0,
  "seasons": [
    {
      "id": 1,
      "season_number": 1,
      "name": "Season 1",
      "episode_count": 7,
      "watched_count": 7,
      "is_complete": true,
      "episodes": [
        {
          "id": 1,
          "episode_number": 1,
          "name": "Pilot",
          "runtime_mins": 58,
          "air_date": "2008-01-20",
          "watched": true,
          "watched_at": "2024-01-15T20:00:00Z"
        }
      ]
    }
  ]
}
```

---

### `GET /shows/in-progress`
Returns all shows that have at least one watched episode but are not fully complete.

**Response `200`:** Array of show summary objects with `remaining_episodes`, `remaining_hours`

---

### `POST /shows/{show_id}/episodes/{episode_id}/watch`
Mark a single episode as watched.

**Body** *(optional)*:
```json
{ "rating": 4, "note": "Great episode" }
```

**Response `201`:** `WatchHistoryEntry`

---

### `DELETE /shows/{show_id}/episodes/{episode_id}/watch`
Unmark a single episode (removes most recent watch entry).

**Response `204`:** No content

---

### `POST /shows/{show_id}/seasons/{season_number}/watch`
Mark all episodes in a season as watched at once.

**Response `201`:**
```json
{ "marked_watched": 7, "already_watched": 0 }
```

---

## Dashboard

### `GET /dashboard`
Returns combined global statistics and recent activity.

**Response `200`:**
```json
{
  "stats": {
    "movies_watched": 42,
    "movie_hours_watched": 84.5,
    "episodes_watched": 310,
    "series_hours_watched": 232.0,
    "in_progress_count": 5,
    "remaining_episodes": 120,
    "remaining_hours": 90.0,
    "series_completed_pct": 38
  },
  "recent_activity": [ ...WatchHistoryEntry... ]
}
```

---

## History

### `GET /history`
Paginated, filterable watch history.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `from_date` | string | — | ISO date or datetime |
| `to_date` | string | — | ISO date or datetime |
| `limit` | int | 100 | Max 500 |
| `offset` | int | 0 | Pagination offset |

**Response `200`:** Array of `WatchHistoryEntry`

---

### `GET /history/stats`
Statistics for a given date range.

**Query params:** Same `from_date` / `to_date` as above.

**Response `200`:**
```json
{
  "movies_watched": 5,
  "movie_hours": 10.5,
  "episodes_watched": 22,
  "series_hours": 16.5,
  "total_hours": 27.0
}
```

---

## Admin

### `GET /admin/sync/trigger`
Manually trigger the background sync job for returning series.

**Response `200`:** `{ "message": "Sync started" }`

---

### `POST /admin/import/trakt`
Import watched movies or TV episodes from a standard Trakt.tv JSON export.
You can upload either the movies JSON array or the shows JSON array to this unified endpoint. The API will automatically detect the format and ingest the items. TMDB IDs are required to fetch missing metadata.

**Expected Payloads:**
- **Movies:** An array of objects where each contains `movie.ids.tmdb` and `last_watched_at`.
- **Shows:** An array of objects where each contains `show.ids.tmdb`, and nested `seasons` -> `episodes` -> `last_watched_at`.

_Fallback Support:_ A dictionary payload containing `{"movies": [...], "episodes": [...]}` is also supported for backward compatibility.

**Body:** Raw JSON upload of `watched-movies.json` or `watched-shows.json` (as multipart/form-data with a `file` field).

**Response `200`:**
```json
{ 
  "imported_movies": 42, 
  "imported_episodes": 310, 
  "skipped": [
    { "title": "Obscure Movie", "reason": "Missing TMDB ID" }
  ] 
}
```

---

## Health

### `GET /health`
Container health check endpoint.

**Response `200`:** `{ "status": "ok" }`

---

## Error Response Format

All error responses follow FastAPI's standard format:
```json
{
  "detail": "Human-readable error message"
}
```

| HTTP Code | Meaning |
|-----------|---------|
| 400 | Bad request / validation error |
| 401 | Not authenticated |
| 403 | Forbidden |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate entry) |
| 422 | Unprocessable entity (schema mismatch) |
| 500 | Internal server error |
| 502 | External API (TMDB) failure |
