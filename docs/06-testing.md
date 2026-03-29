# Testing Guide

---

## Philosophy

Tests target **backend business logic and API contracts** — specifically the areas most likely to regress:

- Authentication flow (login, token issuance)
- Movie add / watch / unwatch lifecycle
- TV show episode progress tracking
- Season-level bulk watch marking
- In-progress and completion detection

External dependencies (TMDB API) are **fully mocked** so tests run fast and consistently without network access.

---

## Stack

| Tool | Purpose |
|------|---------|
| `pytest` | Test runner |
| `pytest-asyncio` | async/await test support |
| `pytest-mock` | Mock/patch TMDB service calls |
| `httpx` + `ASGITransport` | In-process FastAPI test client (no real HTTP) |
| SQLite in-memory | Fresh database per test function |

---

## Running Tests

### Inside Docker (recommended — matches production environment)

```bash
# From the project root
docker compose run --rm -u root -v "$PWD/backend:/app" backend bash -c \
  "pip install -r requirements-test.txt && pytest -v tests/"
```

### On your local machine (requires Python 3.12 + dependencies installed)

```bash
cd backend
pip install -r requirements.txt -r requirements-test.txt
pytest -v tests/
```

---

## Test File Structure

```
backend/tests/
├── conftest.py          # Shared fixtures: DB, client, mock user, TMDB mocks
├── test_auth.py         # Login success, wrong password, /me endpoint
├── test_movies.py       # Add movie, duplicate, mark watched, unwatch, stats
├── test_shows.py        # Add show, mark episode, mark season, in-progress logic
└── test_extended.py     # Search, health, isolation, history stats, admin/import
```

---

## Key Fixtures (`conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `db_session` | function | Fresh in-memory SQLite; schema created before each test, dropped after |
| `client` | function | Unauthenticated HTTPX async client; `get_db` overridden with test session |
| `mock_user` | function | Pre-created `User` row in the test DB |
| `auth_client` | function | Same as `client` but `get_current_user` DI returns `mock_user` |
| `mock_tmdb` | autouse | Patches all `tmdb_service.*` functions globally (no real API calls) |

### TMDB Mock Data

The `mock_tmdb` fixture patches these TMDB service functions with deterministic return values:

| Function | Mock Returns |
|----------|-------------|
| `search_movies` | Empty list `[]` |
| `search_shows` | Empty list `[]` |
| `get_movie_detail` | Movie: "Test Movie", 120-min runtime, tmdb_id=123 |
| `get_show_detail` | Show: "Test Show", 1 season, 2 episodes × 45 min, tmdb_id=456 |

---

## Test Cases

### `test_auth.py`

| Test | Verifies |
|------|---------|
| `test_login_success` | Valid credentials return `access_token` + `token_type: bearer` |
| `test_login_wrong_password` | Returns HTTP 401 |
| `test_get_me_protected` | Authenticated `/auth/me` returns current user's `username` |

### `test_movies.py`

| Test | Verifies |
|------|---------|
| `test_add_movie_success` | POST `/movies` returns 201 with correct title and runtime |
| `test_add_duplicate_movie` | Second add returns 409 Conflict |
| `test_mark_watched_and_history` | Mark watched → history grows → dashboard `movies_watched` increments |
| `test_unwatch_movie` | Delete watch entry → history is empty |

### `test_shows.py`

| Test | Verifies |
|------|---------|
| `test_add_show` | Show added with 2 episodes; `watched_episodes=0`, `remaining_episodes=2` |
| `test_mark_episode_watched` | Single episode watch increments dashboard `episodes_watched`; show appears in in-progress |
| `test_mark_season_watched_completes_show` | Season bulk-watch sets all 2 episodes watched; show NOT in in-progress |

### `test_extended.py`

| Test | Verifies |
|------|---------|
| `test_health_check` | GET `/api/health` returns status: "ok" |
| `test_search_movies/shows` | TMDB search results enrichment; `in_library` check for current user |
| `test_movie_detail` | Detailed metadata fetch for added movie |
| `test_unmark_episode_watched` | Single episode unwatch → stats and history update |
| `test_history_and_stats` | Combined movie/episode history; period-based stats calculation |
| `test_multi_tenant_isolation` | User B cannot see User A's library or statistics |
| `test_admin_sync` | Protected endpoint triggers background sync service |
| `test_trakt_import` | Bulk import from Trakt.tv JSON; upserting media and history entries |

---

## Known Issues & Workarounds

### passlib + bcrypt ≥ 4.0 compatibility

The `passlib` library checks `bcrypt.__about__.__version__` which doesn't exist in bcrypt 4.x.  
**Workaround** is applied in `conftest.py`:

```python
import bcrypt
if not hasattr(bcrypt, "__about__"):
    class AboutMock:
        __version__ = "4.0.1"
    bcrypt.__about__ = AboutMock()
```

This must run before any import of `app.core.security`.

### SQLAlchemy MissingGreenlet error

When a route handler accesses a lazy-loaded ORM relationship after the session has closed, SQLAlchemy raises `MissingGreenlet`. The fix is `expire_on_commit=False` on the test session factory (already configured in `conftest.py`).

---

## Adding New Tests

1. Add a new `test_<feature>.py` file under `backend/tests/`
2. Use `auth_client` fixture for any protected endpoint
3. Use `client` for unauthenticated endpoints
4. TMDB is always mocked — modify `mock_tmdb` in `conftest.py` if you need different mock data
5. Mark the test module: `pytestmark = pytest.mark.asyncio`
