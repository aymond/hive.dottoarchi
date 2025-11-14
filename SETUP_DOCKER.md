# Docker Setup Instructions

## Prerequisites

1. **Docker** and **Docker Compose** must be installed on your system
   - Install Docker Desktop: https://www.docker.com/products/docker-desktop
   - Or install Docker Engine and Docker Compose separately

2. Verify installation:
   ```bash
   docker --version
   docker compose version
   ```

## Setup Steps

### 1. Create Environment File

Create a `.env` file in the project root directory:

```bash
# Copy the example file
cp .env.example .env
```

Or create `.env` manually with the following content:

```env
# Flask secret key (required for session management)
# Generate a secure key with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_secure_secret_key_here

# Debug mode (set to 'true' for development, 'false' for production)
DEBUG=false

# Host and port for the web interface
HOST=0.0.0.0
PORT=5000

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
```

**Important:** Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Build and Start the Application

```bash
# Build and start in detached mode
docker compose up --build -d

# Or use the older docker-compose command:
docker-compose up --build -d
```

### 3. View Logs

```bash
# View logs
docker compose logs -f

# Or for older docker-compose:
docker-compose logs -f
```

### 4. Access the Application

Once started, the web interface will be available at:
- **http://localhost:5000**

### 5. Stop the Application

```bash
# Stop the containers
docker compose down

# Or remove containers and volumes
docker compose down -v
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, you can:
1. Change the port in `docker-compose.yml`:
   ```yaml
   ports:
     - "8080:5000"  # Use port 8080 instead
   ```
2. Or stop the service using port 5000

### Container Fails to Start

1. Check logs:
   ```bash
   docker compose logs
   ```

2. Verify the `.env` file exists and has valid values

3. Rebuild the image:
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

### Permission Issues

If you encounter permission issues:
1. Make sure Docker is running
2. Check that you have permission to access Docker (may need to add user to docker group on Linux)

## Development Mode

For development with auto-reload, you can modify the Dockerfile CMD or run:
```bash
docker compose run --rm dot2archimate dot2archimate web --host 0.0.0.0 --port 5000 --debug
```

## Production Deployment

For production:
1. Set `DEBUG=false` in `.env`
2. Use a strong `SECRET_KEY`
3. Consider using a reverse proxy (nginx, traefik) in front
4. Set up proper logging and monitoring
5. Use Docker secrets or a secrets management system instead of `.env` file

