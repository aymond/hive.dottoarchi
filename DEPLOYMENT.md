# Production Deployment Guide

This guide covers deploying the DOT to ArchiMate Converter to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Docker Setup](#production-docker-setup)
4. [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Environment Configuration](#environment-configuration)
7. [Deployment Options](#deployment-options)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security Best Practices](#security-best-practices)
10. [Scaling and High Availability](#scaling-and-high-availability)
11. [Backup and Recovery](#backup-and-recovery)
12. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- Domain name (for SSL/TLS)
- Basic knowledge of Linux server administration
- SSH access to your production server

## Quick Start

### 1. Clone and Prepare

```bash
git clone <your-repo-url>
cd dot2archimate
```

### 2. Create Production Environment File

```bash
cp .env.example .env.prod
```

Edit `.env.prod` with production values:

```env
# Generate a secure key: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_production_secret_key_here

# Production settings
DEBUG=false
HOST=0.0.0.0
PORT=5000
LOG_LEVEL=INFO

# Gunicorn settings (optional)
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
```

### 3. Deploy with Docker Compose

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### 4. Verify Deployment

```bash
# Check container status
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl http://localhost:5000/health
```

## Production Docker Setup

### Using Production Dockerfile

The `Dockerfile.prod` includes:
- Production WSGI server (Gunicorn)
- Health checks
- Non-root user execution
- Optimized layer caching
- Resource limits

### Build Production Image

```bash
docker build -f Dockerfile.prod -t dot2archimate:prod .
```

### Run Production Container

```bash
docker run -d \
  --name dot2archimate-prod \
  -p 5000:5000 \
  --env-file .env.prod \
  --restart unless-stopped \
  dot2archimate:prod
```

### Using Docker Compose (Recommended)

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Reverse Proxy (Nginx)

### Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### Configuration

1. Copy the nginx configuration:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/dot2archimate
```

2. Update the configuration:
   - Replace `your-domain.com` with your actual domain
   - Update SSL certificate paths (see SSL/TLS section)

3. Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/dot2archimate /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### Key Features

- **Rate Limiting**: 10 requests/second per IP
- **SSL/TLS**: Secure HTTPS connections
- **Security Headers**: HSTS, X-Frame-Options, etc.
- **Health Checks**: Bypass rate limiting for monitoring
- **Static File Caching**: 30-day cache for static assets

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already configured in certbot)
sudo certbot renew --dry-run
```

### Option 2: Self-Signed Certificate (Testing Only)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/dot2archimate.key \
  -out /etc/ssl/certs/dot2archimate.crt
```

Update nginx.conf with the certificate paths.

### Option 3: Commercial Certificate

Upload your certificate files and update paths in `nginx.conf`:
- `ssl_certificate`: Path to fullchain.pem
- `ssl_certificate_key`: Path to privkey.pem

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key (required) | Generated hex string |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `HOST` | Bind host | `0.0.0.0` |
| `PORT` | Bind port | `5000` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GUNICORN_WORKERS` | Number of worker processes | CPU count * 2 + 1 |
| `GUNICORN_THREADS` | Threads per worker | `2` |

### Using Docker Secrets (Production)

For sensitive data, use Docker secrets:

```bash
# Create secret
echo "your_secret_key" | docker secret create secret_key -

# Update docker-compose.prod.yml
secrets:
  - secret_key
```

## Deployment Options

### Option 1: VPS/Cloud Server (DigitalOcean, AWS EC2, etc.)

1. **Provision Server**:
   - Minimum: 2 CPU, 2GB RAM
   - Recommended: 4 CPU, 4GB RAM
   - OS: Ubuntu 22.04 LTS or similar

2. **Initial Setup**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
```

3. **Deploy Application**:
```bash
# Clone repository
git clone <your-repo-url>
cd dot2archimate

# Configure environment
cp .env.example .env.prod
nano .env.prod  # Edit with production values

# Start services
docker compose -f docker-compose.prod.yml up -d
```

4. **Configure Firewall**:
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Option 2: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml dot2archimate

# Check services
docker service ls
```

### Option 3: Kubernetes

Create Kubernetes manifests:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dot2archimate
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dot2archimate
  template:
    metadata:
      labels:
        app: dot2archimate
    spec:
      containers:
      - name: dot2archimate
        image: dot2archimate:prod
        ports:
        - containerPort: 5000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: dot2archimate-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 40
          periodSeconds: 30
```

### Option 4: Cloud Platforms

#### AWS (ECS/Fargate)

1. Push image to ECR
2. Create ECS task definition
3. Deploy to Fargate cluster
4. Configure Application Load Balancer

#### Google Cloud Platform (Cloud Run)

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/dot2archimate

# Deploy
gcloud run deploy dot2archimate \
  --image gcr.io/PROJECT_ID/dot2archimate \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure (Container Instances)

```bash
az container create \
  --resource-group myResourceGroup \
  --name dot2archimate \
  --image dot2archimate:prod \
  --dns-name-label dot2archimate \
  --ports 5000
```

## Monitoring and Logging

### Health Checks

The application provides a `/health` endpoint:

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "storage": "accessible",
  "timestamp": 1234567890.123
}
```

### Logging

#### Docker Logs

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# View last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100
```

#### Centralized Logging

For production, consider:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki + Grafana**
- **CloudWatch** (AWS)
- **Stackdriver** (GCP)

### Monitoring Tools

- **Prometheus + Grafana**: Metrics collection and visualization
- **Uptime Robot**: External uptime monitoring
- **Sentry**: Error tracking
- **New Relic / Datadog**: APM and monitoring

### Metrics to Monitor

- Request rate and latency
- Error rates (4xx, 5xx)
- Container resource usage (CPU, memory)
- Disk usage (session storage)
- Health check status

## Security Best Practices

### 1. Secrets Management

- Never commit `.env` files to version control
- Use environment variables or secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate `SECRET_KEY` regularly

### 2. Network Security

- Use firewall rules to restrict access
- Only expose necessary ports (80, 443)
- Use VPN or SSH tunneling for admin access
- Implement rate limiting (configured in nginx)

### 3. Container Security

- Run containers as non-root user (already configured)
- Keep base images updated
- Scan images for vulnerabilities:
  ```bash
  docker scan dot2archimate:prod
  ```
- Use `--no-new-privileges` flag (in docker-compose.prod.yml)

### 4. Application Security

- Set `DEBUG=false` in production
- Use strong `SECRET_KEY`
- Enable HTTPS only
- Implement security headers (via nginx)
- Regular security updates

### 5. File Upload Security

- Validate file types and sizes
- Scan uploaded files for malware
- Store uploads outside web root
- Implement file size limits (configured in nginx: 10MB)

## Scaling and High Availability

### Horizontal Scaling

1. **Multiple Containers**:

Update `docker-compose.prod.yml`:
```yaml
services:
  dot2archimate:
    deploy:
      replicas: 3
```

2. **Load Balancer**:

Update nginx upstream:
```nginx
upstream dot2archimate_backend {
    server localhost:5000;
    server localhost:5001;
    server localhost:5002;
}
```

3. **Session Storage**:

For multiple instances, use shared storage:
- Redis for session storage (requires code changes)
- Shared volume for file-based sessions
- Database-backed sessions

### Vertical Scaling

Increase resources in `docker-compose.prod.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

### High Availability

- Deploy across multiple availability zones
- Use managed databases for persistent data
- Implement automated failover
- Regular backups (see Backup section)

## Backup and Recovery

### What to Backup

1. **Configuration Files**:
   - `.env.prod`
   - `legal_settings.yaml`
   - Nginx configuration

2. **Persistent Data**:
   - Output files (`/app/output`)
   - Configuration (`/app/dot2archimate/web/config`)

3. **Session Data** (optional, usually ephemeral):
   - `/tmp/dot2archimate_sessions`

### Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/dot2archimate"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup volumes
docker run --rm \
  -v dot2archimate_output:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/output_$DATE.tar.gz -C /data .

# Backup config
docker run --rm \
  -v dot2archimate_config:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/config_$DATE.tar.gz -C /data .

# Backup env file
cp .env.prod $BACKUP_DIR/env_$DATE.prod

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Recovery

```bash
# Restore output volume
docker run --rm \
  -v dot2archimate_output:/data \
  -v /backups/dot2archimate:/backup \
  alpine tar xzf /backup/output_YYYYMMDD_HHMMSS.tar.gz -C /data

# Restore config
docker run --rm \
  -v dot2archimate_config:/data \
  -v /backups/dot2archimate:/backup \
  alpine tar xzf /backup/config_YYYYMMDD_HHMMSS.tar.gz -C /data
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check container status
docker compose -f docker-compose.prod.yml ps

# Verify environment file
cat .env.prod
```

### Health Check Failing

```bash
# Test health endpoint directly
curl http://localhost:5000/health

# Check storage directory permissions
docker exec dot2archimate-prod ls -la /tmp/dot2archimate_sessions
```

### High Memory Usage

- Reduce `GUNICORN_WORKERS`
- Increase container memory limit
- Check for memory leaks in logs

### Slow Performance

- Increase worker/thread count
- Check database/disk I/O
- Review nginx access logs for slow requests
- Consider caching static content

### SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443

# Check certificate expiration
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## Support

For issues and questions:
- Check logs: `docker compose -f docker-compose.prod.yml logs`
- Review this guide
- Open an issue on GitHub

