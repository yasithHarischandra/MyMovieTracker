# Deployment Guide

> Step-by-step instructions to deploy the Personal Media Tracker on a Linux VPS.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Linux VPS | Ubuntu 22.04 LTS recommended |
| Docker Engine ≥ 24 | [Install guide](https://docs.docker.com/engine/install/) |
| Docker Compose v2 | Included with Docker Desktop; `docker compose` (not `docker-compose`) |
| Nginx (host) | `sudo apt install nginx` |
| Certbot | `sudo apt install certbot python3-certbot-nginx` |
| TMDB API Key | Free at [themoviedb.org](https://www.themoviedb.org/settings/api) |
| Domain name | Optional, but required for HTTPS |

---

## Step 1 — Copy Files to the Server

```bash
# From your local machine
scp -r ./mediaTracker user@your-server-ip:~/mediatracker

# Or clone from git if you push it to a repo
ssh user@your-server-ip
git clone <your-repo-url> ~/mediatracker
```

---

## Step 2 — Configure Environment Variables

```bash
cd ~/mediatracker
cp backend/.env.example backend/.env
nano backend/.env
```

**Edit these required values:**

```dotenv
# Required
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
TMDB_API_KEY=<your_tmdb_api_key>

# Required for CORS — use your actual domain or server IP
ALLOWED_ORIGINS=https://your-domain.com,http://your-server-ip

# Optional — change default 30 day token lifetime
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Leave as-is for SQLite
DATABASE_URL=sqlite+aiosqlite:////data/mediatracker.db
```

---

## Step 3 — Build and Start the Container

```bash
cd ~/mediatracker
docker compose up -d --build
```

Verify the container is running:
```bash
docker compose ps
docker compose logs backend --tail=50
```

Test the health endpoint:
```bash
curl http://localhost:8020/api/health
# Expected: {"status":"ok"}
```

---

## Step 4 — Create Your Admin User

```bash
docker compose exec backend python scripts/create_user.py \
  --username admin \
  --password "YourVerySecurePassword123!"
```

You can create additional users with the same command.

---

## Step 5 — Build and Deploy the Frontend

The Vue frontend must be built and served as static files by Nginx.

```bash
cd ~/mediatracker/frontend
npm install
npm run build
```

Copy the built files to the Nginx web root:
```bash
sudo mkdir -p /var/www/mediatracker
sudo cp -r dist/* /var/www/mediatracker/
```

---

## Step 6 — Configure Nginx

Copy the included configuration:
```bash
sudo cp ~/mediatracker/nginx/mediatracker.conf /etc/nginx/sites-available/mediatracker
sudo ln -s /etc/nginx/sites-available/mediatracker /etc/nginx/sites-enabled/
```

Edit the config to set your domain:
```bash
sudo nano /etc/nginx/sites-available/mediatracker
# Replace 'your-domain.com' with your actual domain
```

The default `nginx/mediatracker.conf` proxies `/api/*` to the backend and serves `/` as the Vue SPA:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Vue SPA — serve index.html for all non-API routes
    root /var/www/mediatracker;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API calls to the FastAPI backend container
    location /api/ {
        proxy_pass http://localhost:8020;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Test and reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 7 — Enable HTTPS with Certbot

```bash
sudo certbot --nginx -d your-domain.com
```

Certbot will automatically:
- Obtain an SSL certificate from Let's Encrypt
- Modify the Nginx config to redirect HTTP → HTTPS
- Set up auto-renewal

Test auto-renewal:
```bash
sudo certbot renew --dry-run
```

---

## Updating the Application

```bash
cd ~/mediatracker

# Pull new code (if using git)
git pull

# Rebuild and restart backend
docker compose up -d --build

# Rebuild frontend
cd frontend && npm run build && sudo cp -r dist/* /var/www/mediatracker/
```

Database migrations run automatically on container start (`alembic upgrade head` is in the Docker CMD).

---

## Useful Operations

### View logs
```bash
docker compose logs -f backend
```

### Backup the database
```bash
docker compose exec backend sh -c "sqlite3 /data/mediatracker.db .dump" > backup_$(date +%Y%m%d).sql
```

### Restore from backup
```bash
cat backup_20240101.sql | docker compose exec -T backend sqlite3 /data/mediatracker.db
```

### Manually trigger background sync
```bash
curl -H "Authorization: Bearer <your_token>" http://localhost:8020/api/admin/sync/trigger
```

### Change a user's password
Currently requires recreating the user. An admin password-change endpoint is a planned future enhancement.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | Check `docker compose logs backend` — usually a missing `.env` var |
| 401 on all API calls | Token expired; log in again to get a new one |
| CORS errors | Add your origin to `ALLOWED_ORIGINS` in `.env` and restart container |
| Images not loading | Check `TMDB_API_KEY` is valid |
| Nginx 502 Bad Gateway | Backend container not running; check `docker compose ps` |
| Frontend shows blank page after update | Clear browser cache or do a hard reload (`Ctrl+Shift+R`) |
