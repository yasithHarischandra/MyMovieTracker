# Architecture & Product Decisions Record

> **Date finalized:** 2026-03-28  
> This document captures every key decision made during design and development — *what* was chosen and *why*.

---

## 1. Product Decisions

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| P-1 | Authentication | JWT login; 30-day token stored in `localStorage` | Personal-use app; no session-server overhead |
| P-2 | Ratings & Notes | Optional 1–5 star rating + free-text note per watched entry | Non-intrusive. Both are always nullable |
| P-3 | Episode marking granularity | Single episode **or** entire season at once | Covers both use-cases without extra UI |
| P-4 | Unwatch / delete | Any watch entry can be deleted from history | History is an append-only ledger; deletes are explicit user actions |
| P-5 | Series completion detection | Auto-detected when the last known episode is marked watched | Disappears from In-Progress on next page load — simple, no polling |
| P-6 | Home page / Dashboard | Chronological recent-activity feed + global stats | Quick overview at a glance |
| P-7 | History page | Full feed + date-range filter + per-period stats | Power-user view for retrospective analysis |
| P-8 | Series detail | Per-season progress breakdown; remaining episodes & hours per season and total | Core requirement from SRS |
| P-9 | Trakt.tv migration | One-time JSON import via Settings page | Low-friction migration path; no API key needed |

---

## 2. Authentication Design

- **Library:** `python-jose` for JWT signing; `passlib[bcrypt]` for password hashing
- **Token endpoint:** `POST /api/auth/token` → returns `{ access_token, token_type }`
- **Token lifetime:** 30 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`)
- **User creation:** CLI script only — no public registration endpoint
  ```bash
  docker compose exec backend python scripts/create_user.py --username admin --password "secret"
  ```
- **Frontend:** Axios instance auto-attaches `Authorization: Bearer <token>` to all API calls via Pinia auth store

---

## 3. Scheduler — APScheduler

| Option | Verdict |
|--------|---------|
| FastAPI `BackgroundTasks` | ❌ No periodic/cron scheduling |
| **APScheduler `AsyncIOScheduler`** | ✅ Selected |
| Celery + Redis | ❌ Doubles infra footprint for a personal app |

- **Schedule:** Tuesday & Friday at **02:00 UTC** (historically low traffic slot)
- Started on FastAPI `lifespan` startup; in-memory — a missed sync on container restart is harmless
- Targets only shows where TMDB `status = "Returning Series"` to avoid unnecessary API calls

---

## 4. TMDB API Integration

- **API version:** v3 with `api_key` query parameter (env var `TMDB_API_KEY`)
- **Poster images:** Served directly from `https://image.tmdb.org/t/p/w500/<path>` — no local storage or caching
- **On "Add Movie":** Fetches title, overview, release_date, runtime, genres, poster_path, tmdb_id
- **On "Add Show":** Fetches show metadata + **all seasons and episodes** in parallel (skips Season 0 specials)
- **Episode runtime fallback:** Defaults to 45 minutes when TMDB returns null

---

## 5. Database Decisions

| Concern | Decision |
|---------|----------|
| Engine | **SQLite** (single file, zero-ops, perfect for personal use) |
| ORM | SQLAlchemy 2.x async + `aiosqlite` driver |
| Migrations | Alembic from day one |
| Future migration path | Change `DATABASE_URL` in `.env` + run `alembic upgrade head` → PostgreSQL support with zero code change |

### Schema Overview

| Table | Purpose |
|-------|---------|
| `users` | Auth credentials; `user_id` FK on all user-owned tables |
| `movies` | TMDB movie metadata |
| `tv_shows` | TMDB show metadata |
| `seasons` | Season records per show |
| `episodes` | Episode records per season |
| `watch_history` | Append-only ledger (movie **or** episode) with timestamp, optional rating & note |

---

## 6. Frontend Decisions

| Topic | Decision |
|-------|----------|
| Framework | **Vue 3** (Composition API + `<script setup>`) + Vite |
| Styling | **Tailwind CSS v3** (v4 reverted — breaking PostCSS API at build time) |
| HTTP client | **Axios** with a shared instance that auto-injects JWT |
| State management | **Pinia** |
| Routing | **Vue Router 4** with navigation guards for auth |
| Icons | `@phosphor-icons/vue` — all imports use `Ph` prefix |
| Theme | Dark-mode-first, cinematic aesthetic; Inter + JetBrains Mono fonts |

---

## 7. Infrastructure Decisions

| Topic | Decision |
|-------|----------|
| Backend port | **8020** (host-mapped) |
| Container | Single Docker container — FastAPI + uvicorn |
| Static files | Vue `dist/` served by **host Nginx** (not containerized) |
| SSL | Host Nginx + **Certbot** |
| DB persistence | SQLite mounted at `/data/mediatracker.db` via named Docker volume `mediatracker-data` |
| Nginx routing | `/api/` → proxy to localhost:8020; `/*` → Vue SPA static files |

---

## 8. Extensibility Strategy

| Concern | Strategy |
|---------|----------|
| Switch to PostgreSQL | Change `DATABASE_URL` in `.env`; run `alembic upgrade head` — zero application code change |
| Multi-user support | `user_id` FK already on all content tables; add a registration endpoint when needed |
| Cloud TMDB image caching | Add a background job to download & serve poster images locally (no schema change required) |
| External metadata provider | `tmdb_service.py` is the single integration point; swap it out without touching routers or services |
