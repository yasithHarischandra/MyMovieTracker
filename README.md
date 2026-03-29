# Personal Media Tracker

A self-hosted, lightweight alternative to Trakt.tv, built with FastAPI, Vue 3, and SQLite.

## Features

- **Watch Tracking:** Keep track of movies and TV episodes you've watched.
- **In-Progress Series:** Automatically track and sort TV series that you are currently watching.
- **Statistics & History:** View your watch history timeline and global statistics (hours watched, episodes watched, etc.).
- **TMDB Integration:** Seamlessly search and import metadata for movies and TV shows from The Movie Database (TMDB).
- **Automated Sync:** Background tasks automatically fetch new episodes and season updates for returning series.
- **Trakt.tv Import:** Easily migrate your watch history from Trakt.tv using a JSON export.

## Architecture

- **Backend:** Python + FastAPI + SQLAlchemy 2.0 (Async)
- **Database:** SQLite using `aiosqlite` (single-file database, perfect for personal self-hosting)
- **Frontend:** Vue 3 + Tailwind CSS + Vite
- **Infrastructure:** Docker & Docker Compose with Nginx as a reverse proxy

## Prerequisites

- Linux Server (VPS or local machine)
- Docker & Docker Compose installed
- A free TMDB API Key (from themoviedb.org)
- Domain name pointing to your server IP (optional, for SSL/Nginx)

## Deployment Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url> mediatracker
   cd mediatracker
   ```

2. **Configure Environment Variables:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your TMDB_API_KEY and a secure SECRET_KEY
   ```
   **Important:** Update `ALLOWED_ORIGINS` in the `.env` if deploying to a custom domain (e.g., `https://your-domain.com`). By default, it allows `http://localhost:5173` and `http://localhost`.

3. **Deploy with Docker Compose:**
   ```bash
   # This will build the frontend, backend, and start the containers in detached mode
   docker compose up -d --build
   ```

4. **Create the Initial Admin User:**
   ```bash
   # Execute the CLI script inside the backend container to create your login
   docker compose exec backend python scripts/create_user.py --username admin --password "YourSecurePassword"
   ```

5. **Nginx Reverse Proxy & SSL (Optional but Recommended):**
   - The included `nginx/mediatracker.conf` provides a boilerplate for reverse proxying traffic.
   - Use Certbot (`sudo certbot --nginx`) to automatically obtain and configure SSL certificates for your domain.

## Usage

1. Navigate to `http://localhost` (or your domain).
2. Log in with the admin credentials you created.
3. Start searching for movies and TV shows to add to your library!

## Migrating from Trakt.tv

1. Go to Trakt.tv and request a GDPR Data Export.
2. Once you receive the zip file, extract it and locate the `.json` files (e.g., `watched_movies.json`, `watched_shows.json`).
3. In the Media Tracker, navigate to **Settings** -> **Trakt.tv JSON Import**.
4. Upload your JSON files one by one. The backend will process the files, match the TMDB IDs, and retroactively log your watch history.
