# CineTrack

A self-hosted, lightweight personal media tracker, built with FastAPI, Vue 3, and SQLite.

## Features

- **Watch Tracking:** Keep track of movies and TV episodes you've watched.
- **In-Progress Series:** Automatically track and sort TV series that you are currently watching.
- **Statistics & History:** View your watch history timeline and global statistics.
- **TMDB Integration:** Seamlessly search and import metadata from The Movie Database (TMDB).
- **Automated Sync:** Background tasks automatically fetch new episodes and season updates.
- **Trakt.tv Import:** Easily migrate your watch history from Trakt.tv using a JSON export.

## Architecture

- **Backend:** Python + FastAPI + SQLAlchemy 2.0 (Async)
- **Database:** SQLite using `aiosqlite`
- **Frontend:** Vue 3 + Tailwind CSS + Vite
- **Infrastructure:** Unified Docker container with Nginx serving the frontend and proxying the backend.

## Deployment Instructions

### 1. Configure Environment Variables
Create a `.env` file in the project root:
```bash
SECRET_KEY=your_secure_random_string
TMDB_API_KEY=your_tmdb_api_key
```

### 2. Deploy with Docker
The recommended way to deploy CineTrack is using the unified Docker image from GitHub Container Registry (GHCR).

#### Using Docker Compose (Recommended)
```yaml
services:
  cinetrack:
    image: ghcr.io/<your-username>/cinetrack:latest
    ports:
      - "80:80"
    volumes:
      - cinetrack-data:/data
    env_file: .env
    restart: unless-stopped
```

Run with:
```bash
docker compose up -d
```

#### Using Docker Run
```bash
docker run -d \
  -p 80:80 \
  -v cinetrack-data:/data \
  --env-file .env \
  --name cinetrack \
  ghcr.io/<your-username>/cinetrack:latest
```

### 3. Create the Initial Admin User
```bash
docker exec -it cinetrack python scripts/create_user.py --username admin --password "YourSecurePassword"
```

## Building from Source

To build and run the unified container locally:
```bash
docker build -t cinetrack .
docker run -d -p 80:80 --env-file .env cinetrack
```

## Pushing to GHCR.io

To build and push your own image to GHCR:
```bash
docker build -t ghcr.io/<your-username>/cinetrack:latest .
docker push ghcr.io/<your-username>/cinetrack:latest
```
