# Deployment Guide: MediaTracker on Ubuntu 24.04

This guide provides a step-by-step walkthrough for deploying both the FastAPI backend and Vue.js frontend on a clean Ubuntu 24.04 server.

---

## 1. Prerequisites

### Server Access
- A remote VM with Ubuntu 24.04.
- A user with `sudo` privileges.
- Port 80 (HTTP) and 443 (HTTPS) open on your firewall.

### Install System Dependencies
Update your system and install the required tools:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git nodejs npm
```

---

## 2. Project Setup

Clone your repository into the `/var/www` directory:

```bash
sudo mkdir -p /var/www/mediatracker
sudo chown $USER:$USER /var/www/mediatracker
git clone <your-repo-url> /var/www/mediatracker
cd /var/www/mediatracker
```

---

## 3. Backend Deployment (FastAPI)

### Virtual Environment & Dependencies
```bash
cd /var/www/mediatracker/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn uvicorn
```

### Environment Configuration
Create the `.env` file from the example:

```bash
cp .env.example .env
nano .env
```

**Crucial variables to set:**
- `DATABASE_URL`: For production, use a persistent SQLite path like `sqlite+aiosqlite:////var/www/mediatracker/backend/production.db` or a PostgreSQL URI.
- `SECRET_KEY`: Generate a long random string.
- `TMDB_API_KEY`: Your valid TMDB API key.

### Database Migration
Apply the database schema:

```bash
alembic upgrade head
```

### Systemd Service (Process Management)
Create a systemd service file to keep the backend running:

```bash
sudo nano /etc/systemd/system/mediatracker-backend.service
```

Paste the following:

```ini
[Unit]
Description=MediaTracker FastAPI Backend
After=network.target

[Service]
User=<your-ubuntu-username>
Group=www-data
WorkingDirectory=/var/www/mediatracker/backend
EnvironmentFile=/var/www/mediatracker/backend/.env
ExecStart=/var/www/mediatracker/backend/.venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable mediatracker-backend
sudo systemctl start mediatracker-backend
```

---

## 4. Frontend Deployment (Vue.js)

### Build the Production Assets
```bash
cd /var/www/mediatracker/frontend
npm install
```

Ensure `frontend/src/api/client.js` is configured to point to your production URL or relative `/api` path. Then build:

```bash
npm run build
```

The production files will be generated in `/var/www/mediatracker/frontend/dist`.

---

## 5. Nginx Configuration

Create a site configuration file:

```bash
sudo nano /etc/nginx/sites-available/mediatracker
```

Paste the following:

```nginx
server {
    listen 80;
    server_name your-domain.com; # Or your server IP

    # Frontend
    location / {
        root /var/www/mediatracker/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/mediatracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6. SSL Implementation (Recommended)

Use Certbot to obtain a free SSL certificate from Let's Encrypt:

```bash
sudo apt install snapd
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d your-domain.com
```

---

## 7. Troubleshooting

- **Check Backend Logs:** `journalctl -u mediatracker-backend -f`
- **Check Nginx Error Logs:** `sudo tail -f /var/log/nginx/error.log`
- **Permissions:** Ensure `www-data` has read access to the `dist` folder and the database file.
