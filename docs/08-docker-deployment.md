# Docker Deployment Guide: Unified Container

MediaTracker can be run as a single, unified Docker container containing both the frontend and the backend.

---

## 1. Quick Start (Standalone)

### Build the Image
From the project root:
```bash
docker build -t mediatracker .
```

### Run the Container
```bash
docker run -d \
  -p 8080:80 \
  -v mediatracker-data:/data \
  -e TMDB_API_KEY=your_api_key \
  -e SECRET_KEY=your_secret_key \
  --name mediatracker \
  mediatracker
```
The app will be available at `http://localhost:8080`.

---

## 2. Production Setup (Behind Host Nginx)

If you are running this on a VPS that already has Nginx installed on the host OS, follow this setup.

### Run with Docker Run
Bind the container to `127.0.0.1` so it's not exposed directly to the internet:
```bash
docker run -d \
  --name mediatracker \
  -p 127.0.0.1:8020:80 \
  -v mediatracker-data:/data \
  -e TMDB_API_KEY=your_api_key \
  -e SECRET_KEY=your_secret_key \
  --restart unless-stopped \
  mediatracker
```

### Run with Docker Compose
```yaml
services:
  mediatracker:
    image: ghcr.io/your-username/mediatracker:latest
    # Bind to localhost only so Host Nginx can proxy to it
    ports:
      - "127.0.0.1:8020:80"
    volumes:
      - mediatracker-data:/data
    environment:
      - TMDB_API_KEY=your_api_key
      - SECRET_KEY=your_secret_key
      - DATABASE_URL=sqlite+aiosqlite:////data/mediatracker.db
    restart: unless-stopped

volumes:
  mediatracker-data:
```

### Host Nginx Configuration
Create `/etc/nginx/sites-available/cinetrack`:
```nginx
server {
    listen 80;
    server_name cinetrack.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Required for Trakt JSON imports
        client_max_body_size 55M;
    }
}
```

---

## 3. Pushing to GHCR.io

### 1. Login to GHCR
```bash
echo $CR_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 2. Tag and Push
```bash
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/mediatracker:latest .
docker push ghcr.io/YOUR_GITHUB_USERNAME/mediatracker:latest
```

---

## 4. Configuration Reference

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/mediatracker.db` | Path to the SQLite database inside the container. |
| `TMDB_API_KEY` | (Required) | Your API key from themoviedb.org. |
| `SECRET_KEY` | (Required) | A long random string for auth tokens. |
