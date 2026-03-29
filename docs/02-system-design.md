# System Design

> This document describes the approved architecture and component design for the Personal Media Tracker.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        VPS (Host)                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Nginx (Host Process)                     │  │
│  │   Port 80/443                                         │  │
│  │   /api/*  ──proxy──►  localhost:8020                 │  │
│  │   /*      ──static──►  /var/www/mediatracker/dist    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Docker Container: backend                     │  │
│  │                                                       │  │
│  │   FastAPI (uvicorn)  :8020                           │  │
│  │   ├── APScheduler (background sync job)              │  │
│  │   └── SQLite  ←── Docker volume: mediatracker-data  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          │
          ▼ (outbound)
     TMDB API v3  (metadata fetch & sync)
```

---

## Backend Architecture

### Layer Responsibility Model

```
Request
  │
  ▼
Router  (input validation via Pydantic schemas, HTTP status codes)
  │
  ▼
Service  (business logic, TMDB calls, DB queries)
  │
  ▼
SQLAlchemy ORM  (async session, models)
  │
  ▼
SQLite / aiosqlite
```

### Module Layout

```
backend/
├── app/
│   ├── main.py               # App factory, middleware, router wiring
│   ├── config.py             # Pydantic Settings (env vars)
│   ├── database.py           # Async engine + session factory
│   ├── core/
│   │   ├── security.py       # JWT creation/verification, bcrypt helpers
│   │   ├── dependencies.py   # FastAPI DI: get_db, get_current_user
│   │   ├── middleware.py     # SecurityHeadersMiddleware
│   │   └── scheduler.py      # APScheduler setup & cron jobs
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── movie.py
│   │   ├── tv_show.py
│   │   ├── season.py
│   │   ├── episode.py
│   │   └── watch_history.py
│   ├── schemas/              # Pydantic request/response models
│   │   ├── movie.py
│   │   ├── show.py
│   │   ├── watch.py
│   │   └── stats.py
│   ├── routers/              # FastAPI route handlers (thin layer)
│   │   ├── auth.py
│   │   ├── movies.py
│   │   ├── shows.py
│   │   ├── search.py
│   │   ├── dashboard.py
│   │   ├── history.py
│   │   └── admin.py
│   └── services/             # Business logic (thick layer)
│       ├── auth_service.py
│       ├── movie_service.py
│       ├── show_service.py
│       ├── stats_service.py
│       ├── sync_service.py
│       ├── import_service.py
│       └── tmdb_service.py
├── alembic/                  # Database migrations
├── scripts/
│   └── create_user.py        # CLI user creation
├── tests/                    # Automated test suite
└── requirements.txt
```

---

## Database Schema

### Entity Relationship Diagram

```
users
 ├── id (PK)
 ├── username (unique)
 └── hashed_password

movies
 ├── id (PK)
 ├── user_id (FK → users)
 ├── tmdb_id
 ├── title, overview, release_date
 ├── runtime_mins, genres, poster_path
 └── added_at
     │
     └──► watch_history (movie_id)

tv_shows
 ├── id (PK)
 ├── user_id (FK → users)
 ├── tmdb_id, name, overview
 ├── first_air_date, status, genres, poster_path
 └── added_at
     │
     └──► seasons
           ├── id (PK)
           ├── show_id (FK → tv_shows)
           ├── season_number, name, episode_count, air_date
           └──► episodes
                 ├── id (PK)
                 ├── season_id (FK → seasons)
                 ├── episode_number, name, runtime_mins, air_date
                 └──► watch_history (episode_id)

watch_history  (append-only ledger)
 ├── id (PK)
 ├── user_id (FK → users)
 ├── movie_id (FK → movies, nullable)
 ├── episode_id (FK → episodes, nullable)
 ├── watched_at (timestamptz, server default = now)
 ├── rating (1–5, nullable)
 └── note (text, nullable)
```

**Constraint:** Exactly one of `movie_id` / `episode_id` must be non-null per row (enforced at service layer).

---

## Frontend Architecture

### Component Hierarchy

```
App.vue
├── AppNav.vue            (persistent navigation bar)
└── <RouterView>
    ├── DashboardView.vue
    │   ├── StatCard.vue  (movie stats, series stats)
    │   ├── InProgressCard.vue
    │   └── ActivityFeed.vue
    ├── SearchView.vue
    │   └── MediaCard.vue
    ├── HistoryView.vue
    │   ├── DateRangePicker.vue
    │   ├── PeriodStats.vue
    │   └── WatchHistoryRow.vue
    ├── InProgressView.vue
    │   └── ShowProgressCard.vue
    ├── MovieDetailView.vue
    │   └── WatchHistoryRow.vue
    ├── ShowDetailView.vue
    │   ├── SeasonAccordion.vue
    │   └── EpisodeRow.vue
    └── SettingsView.vue
```

### State Management (Pinia Stores)

| Store | Responsibility |
|-------|---------------|
| `useAuthStore` | JWT token, login/logout, `currentUser` |
| `useMediaStore` | In-memory cache for search results |

### API Communication

- All API calls use a shared Axios instance configured in `src/api/client.js`
- JWT automatically injected via request interceptor
- 401 responses trigger automatic logout and redirect to `/login`

---

## Security Model

| Layer | Control |
|-------|---------|
| Transport | HTTPS via Certbot on host Nginx |
| Authentication | JWT (HS256); 30-day expiry |
| Password storage | bcrypt with cost factor 12 |
| Input validation | Pydantic schemas on every endpoint |
| SQL injection | SQLAlchemy ORM parameterized queries only |
| XSS (note field) | Stripped to plain text before storage |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` via custom middleware |
| CORS | Strict whitelist via `ALLOWED_ORIGINS` env var |

---

## Background Sync Design

```
APScheduler (cron: Tue & Fri @ 02:00 UTC)
    │
    ▼
sync_service.get_returning_shows()
    │  SELECT tv_shows WHERE status='Returning Series'
    ▼
For each show:
    tmdb_service.get_show_detail(tmdb_id)
    │  ► Checks for new seasons / episodes
    ▼
    show_service.update_show_episodes()
    │  ► Inserts new Season + Episode rows
    │  ► Updates show.status if changed
    ▼
    commit()
```

Existing watch history is **never modified** by the sync job.

---

## Trakt.tv Import Flow

```
User uploads JSON file (Settings page)
    │
    ▼
POST /api/admin/import/movies  or  /api/admin/import/shows
    │
    ▼
import_service.process_trakt_export(data)
    │  ► Iterate Trakt watch events
    │  ► Resolve TMDB ID (Trakt provides it in export)
    │  ► Upsert Movie/Show/Season/Episode records
    │  ► Insert WatchHistory rows with original Trakt timestamps
    ▼
Return { imported, skipped, errors } summary
```
