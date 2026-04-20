# Full Deployment Guide

> Step-by-step instructions to deploy CineTrack on a Linux VPS using Docker.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Linux VPS | Ubuntu 22.04+ recommended |
| Docker Engine ≥ 24 | [Install guide](https://docs.docker.com/engine/install/) |
| Docker Compose v2 | `docker compose` |
| TMDB API Key | Free at [themoviedb.org](https://www.themoviedb.org/settings/api) |
| Domain name | Required for HTTPS |

---

## Step 1 — Project Setup

Create a directory for CineTrack and set up your environment variables:

```bash
mkdir -p ~/cinetrack
cd ~/cinetrack
nano .env
```

**Required values for `.env`:**

```dotenv
# Generate a secure key with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_generated_secret_key

# Your TMDB API Key
TMDB_API_KEY=your_tmdb_api_key

# Optional: SQLite Database path (defaults to /data/mediatracker.db)
# DATABASE_URL=sqlite+aiosqlite:////data/mediatracker.db
```

---

## Step 2 — Deploy with Docker Compose

Create a `docker-compose.yml` file:

```bash
nano docker-compose.yml
```

Paste the following configuration:

```yaml
services:
  cinetrack:
    image: ghcr.io/<your-username>/cinetrack:latest
    ports:
      - "127.0.0.1:8020:80" # Bind to localhost to match host Nginx proxy
    volumes:
      - cinetrack-data:/data
    env_file: .env
    restart: unless-stopped

volumes:
  cinetrack-data:
```

Start the container:
```bash
docker compose up -d
```

Verify it's running:
```bash
docker compose ps
curl http://localhost:8020/api/health
```

---

## Step 3 — Create Your Admin User

Run the admin creation script inside the running container:

```bash
docker compose exec cinetrack python scripts/create_user.py \
  --username admin \
  --password "YourSecurePassword123!"
```

---

## Step 4 — Host Nginx & SSL (Recommended)

If you have a domain, use Nginx on your host machine to handle SSL and proxy traffic to the Docker container.

### Install Nginx and Certbot
```bash
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx
```

### Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/cinetrack
```

```nginx
server {
    listen 80;
    server_name cinetrack.duckdns.org www.cinetrack.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Required for large Trakt.tv JSON imports
        client_max_body_size 75M;
    }
}
```

Enable the site and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/cinetrack /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Obtain SSL Certificate
```bash
sudo certbot --nginx -d cinetrack.duckdns.org -d www.cinetrack.duckdns.org
```

---

## Updating CineTrack

To update to the latest version:

```bash
cd ~/cinetrack
docker compose pull
docker compose up -d
```

Database migrations are automatically applied on container startup.

---

## Useful Commands

| Action | Command |
| :--- | :--- |
| **View Logs** | `docker compose logs -f` |
| **Restart** | `docker compose restart` |
| **Shell Access** | `docker compose exec -it cinetrack bash` |
| **Database Backup** | `docker compose exec cinetrack sqlite3 /data/mediatracker.db .dump > backup.sql` |
