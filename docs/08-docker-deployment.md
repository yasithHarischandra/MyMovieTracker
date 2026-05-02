# Docker Deployment: Unified Container

CineTrack is distributed as a single, unified Docker image that includes both the Vue.js frontend (served by Nginx) and the FastAPI backend.

---

## 1. Local Development / Build

### Build the Unified Image
From the project root:
```bash
docker build -t cinetrack:latest .
```

### Run Locally
```bash
docker run -d \
  -p 8080:80 \
  -v cinetrack-data:/data \
  -e TMDB_API_KEY=your_key \
  -e SECRET_KEY=your_secret \
  --name cinetrack \
  cinetrack:latest
```
Visit `http://localhost:8080` in your browser.

---

## 2. GitHub Container Registry (GHCR.io)

### Login to GHCR
First, create a GitHub Personal Access Token (PAT) with `write:packages` and `read:packages` permissions.

```bash
echo $CR_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### Tag and Push the Image
```bash
# Tag for your GitHub repository
docker tag cinetrack:latest ghcr.io/YOUR_GITHUB_USERNAME/cinetrack:latest

# Push to GHCR
docker push ghcr.io/YOUR_GITHUB_USERNAME/cinetrack:latest
```

---

## 3. Deployment Configuration

### Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/mediatracker.db` | SQLite database location inside the container. |
| `TMDB_API_KEY` | (Required) | Your API key from themoviedb.org. |
| `SECRET_KEY` | (Required) | Random hex string for JWT tokens. |
| `PORT` | `80` | Port Nginx listens on inside the container. |

### Docker Compose Example
```yaml
services:
  cinetrack:
    image: ghcr.io/<your-username>/cinetrack:latest
    ports:
      - "127.0.0.1:8020:80" # Bind to localhost to match host Nginx proxy
    volumes:
      - cinetrack-data:/data
    environment:
      - TMDB_API_KEY=${TMDB_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped

volumes:
  cinetrack-data:
```

---

## 4. Internal Architecture

The unified image uses a multi-stage build:
1.  **Stage 1 (Node.js):** Compiles the Vue frontend into static assets in `/frontend/dist`.
2.  **Stage 2 (Python):** Installs the FastAPI backend and Nginx.
3.  **Final:** Copies the frontend assets to `/usr/share/nginx/html`.
4.  **Entrypoint:** Runs `alembic upgrade head`, starts Nginx, and starts Gunicorn.

The Nginx configuration inside the container:
- Serves static files for the frontend.
- Proxies `/api/` requests to the local backend process on port `8020`.


