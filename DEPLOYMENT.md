# Deployment Guide

This guide covers different deployment strategies for the OCR PDF application.

## Table of Contents

1. [Option 1: Separate Hosting (Recommended)](#option-1-separate-hosting-recommended)
2. [Option 2: Single Server (FastAPI serves React)](#option-2-single-server-fastapi-serves-react)
3. [Docker Deployment](#docker-deployment)
4. [Production Checklist](#production-checklist)

---

## Option 1: Separate Hosting (Recommended)

Deploy frontend and backend independently for better scalability and performance.

### Architecture

```
┌──────────────────┐
│  Static Hosting  │  Frontend (Netlify, Vercel, S3+CloudFront)
│  React SPA       │  https://app.yourdomain.com
└────────┬─────────┘
         │ HTTPS/REST
         ▼
┌──────────────────┐
│  Backend Server  │  API (AWS ECS, Cloud Run, DigitalOcean)
│  FastAPI + RQ    │  https://api.yourdomain.com
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Redis           │  Worker queue
└──────────────────┘
```

### Benefits

- ✅ **CDN**: Automatic edge caching for frontend assets
- ✅ **Scalability**: Scale backend independently
- ✅ **Cost**: Static hosting is cheap/free (Netlify, Vercel)
- ✅ **Performance**: Faster global access
- ✅ **Security**: Separate API domain

### Frontend Setup

**1. Configure API endpoint:**

```typescript
// frontend/src/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
```

**2. Create environment files:**

```bash
# frontend/.env.production
VITE_API_URL=https://api.yourdomain.com/api/v1
```

**3. Build:**

```bash
cd frontend
npm run build
# Output in dist/
```

**4. Deploy to static hosting:**

**Netlify:**
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

**Vercel:**
```bash
npm install -g vercel
vercel --prod
```

**AWS S3 + CloudFront:**
```bash
aws s3 sync dist/ s3://your-bucket-name/
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Backend Setup

**1. Update CORS for production:**

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.yourdomain.com",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Deploy backend:**

**DigitalOcean App Platform:**
- Connect your GitHub repo
- Configure: Python 3.11, `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Add Redis as managed database
- Set environment variables

**AWS ECS/Fargate:**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Google Cloud Run:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/ocr-backend
gcloud run deploy ocr-backend \
  --image gcr.io/PROJECT_ID/ocr-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Option 2: Single Server (FastAPI serves React)

Deploy everything together on one server. Simpler but less scalable.

### Architecture

```
┌─────────────────────────┐
│   Single Server         │
│  ┌──────────────────┐   │
│  │  FastAPI         │   │  Port 8000
│  │  - Serves API    │   │
│  │  - Serves React  │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │  RQ Worker       │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │  Redis           │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

### Benefits

- ✅ **Simplicity**: One deployment, no CORS
- ✅ **Cost**: Single server to manage
- ✅ **Good for**: Internal tools, MVPs, small scale

### Drawbacks

- ❌ No CDN benefits
- ❌ Backend must handle static file serving
- ❌ Coupled deployments

### Setup Steps

**1. Build frontend:**

```bash
cd frontend
npm run build
```

**2. Copy frontend to backend:**

```bash
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
```

**3. Update frontend API calls:**

```typescript
// frontend/src/api.ts
// Use relative URLs (same origin)
const API_BASE_URL = '/api/v1';
```

Then rebuild: `npm run build`

**4. Start with integrated server:**

```bash
cd backend
uvicorn serve_frontend:app --host 0.0.0.0 --port 8000
```

Now both API and frontend are served from port 8000:
- Frontend: `http://localhost:8000/`
- API: `http://localhost:8000/api/v1/...`
- Docs: `http://localhost:8000/api/docs`

**5. Setup script:**

```bash
#!/bin/bash
# deploy-single.sh

set -e

echo "Building frontend..."
cd frontend
npm install
npm run build

echo "Copying frontend to backend..."
cd ..
mkdir -p backend/static
rm -rf backend/static/*
cp -r frontend/dist/* backend/static/

echo "Starting server..."
cd backend
source venv/bin/activate
uvicorn serve_frontend:app --host 0.0.0.0 --port 8000
```

---

## Docker Deployment

### Option 1: Separate Containers

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite:///./data/ocr_dev.db
      - FOLDER_PATH=/pdfs
    volumes:
      - ./pdfs:/pdfs
      - ./backend/storage:/app/storage
      - backend-data:/app/data
    depends_on:
      - redis

  worker:
    build: ./backend
    command: rq worker app.workers --url redis://redis:6379/0
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite:///./data/ocr_dev.db
      - FOLDER_PATH=/pdfs
    volumes:
      - ./pdfs:/pdfs
      - ./backend/storage:/app/storage
      - backend-data:/app/data
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1

volumes:
  redis-data:
  backend-data:
```

**Backend Dockerfile:**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY serve_frontend.py .

# Create data directory
RUN mkdir -p /app/data /app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf:**

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
}
```

### Option 2: Single Container

**Dockerfile:**

```dockerfile
# Combined Dockerfile
FROM python:3.11-slim AS backend-base

WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Build frontend
COPY frontend /frontend
WORKDIR /frontend
RUN npm install && npm run build

# Setup backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/serve_frontend.py .

# Copy built frontend
RUN mkdir -p static
RUN cp -r /frontend/dist/* ./static/

EXPOSE 8000

CMD ["uvicorn", "serve_frontend:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Production Checklist

### Security

- [ ] Enable HTTPS (Let's Encrypt, CloudFlare)
- [ ] Configure CORS properly (no `allow_origins=["*"]`)
- [ ] Add authentication (JWT, OAuth)
- [ ] Set secure environment variables
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable rate limiting
- [ ] Validate all user inputs
- [ ] Use security headers (HSTS, CSP)

### Performance

- [ ] Enable Gunicorn/Uvicorn workers: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`
- [ ] Configure Redis persistence
- [ ] Add database connection pooling
- [ ] Enable response compression
- [ ] Use CDN for frontend assets
- [ ] Configure caching headers
- [ ] Monitor with APM (New Relic, DataDog)

### Reliability

- [ ] Set up health checks
- [ ] Configure auto-restart (systemd, supervisord)
- [ ] Enable logging (structured JSON logs)
- [ ] Set up error tracking (Sentry)
- [ ] Configure backups (DB, storage)
- [ ] Set up monitoring/alerting
- [ ] Document runbooks

### Configuration

```bash
# backend/.env.production
AUTO_INGEST=true
FOLDER_PATH=/data/pdfs
INCLUDE_SUBFOLDERS=true
DATABASE_URL=postgresql://user:pass@db:5432/ocrpdf
REDIS_URL=redis://redis:6379/0
STORAGE_PATH=/data/storage
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/ocr-backend.service
[Unit]
Description=OCR PDF Backend
After=network.target redis.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/ocr-pdf/backend
Environment="PATH=/opt/ocr-pdf/backend/venv/bin"
ExecStart=/opt/ocr-pdf/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/ocr-worker.service
[Unit]
Description=OCR PDF Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ocr-pdf/backend
Environment="PATH=/opt/ocr-pdf/backend/venv/bin"
ExecStart=/opt/ocr-pdf/backend/venv/bin/rq worker app.workers
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ocr-backend ocr-worker
sudo systemctl start ocr-backend ocr-worker
```

---

## Recommendation

**For production**: Use **Option 1 (Separate Hosting)**
- Frontend on Netlify/Vercel (free tier works great)
- Backend on DigitalOcean App Platform or AWS ECS
- Managed Redis (DigitalOcean, AWS ElastiCache)

**For internal tools/MVP**: Use **Option 2 (Single Server)**
- Simpler deployment
- Good enough for <1000 users
- Easy to migrate later

**For enterprise**: Add Kubernetes
- Use Helm charts
- Horizontal pod autoscaling
- Managed services (RDS, ElastiCache)

