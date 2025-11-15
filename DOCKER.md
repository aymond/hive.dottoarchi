# Docker Guide for DOT to ArchiMate Converter

This guide provides detailed instructions for using the DOT to ArchiMate Converter with Docker.

## Building the Docker Image

You can build the Docker image locally:

```bash
docker build -t dot2archimate .
```

## Running the Container

### Web Interface

The default command runs the web interface:

```bash
docker run -p 5000:5000 dot2archimate
```

The web interface will be available at http://localhost:5000

### Command Line Interface

You can run any dot2archimate command by passing it as arguments:

```bash
# Convert a DOT file to ArchiMate XML
docker run -v $(pwd):/app/data dot2archimate convert -i /app/data/input.dot -o /app/data/output.xml

# Batch convert multiple files
docker run -v $(pwd):/app/data dot2archimate batch-convert -i /app/data/input -o /app/data/output

# Configure legal settings
docker run -it -v $(pwd)/config:/app/dot2archimate/web/config dot2archimate legal-config --create
```

## Mounting Volumes

To persist data and access files easily, mount volumes:

```bash
docker run -p 5000:5000 \
  -v $(pwd)/examples:/app/examples \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config:/app/dot2archimate/web/config \
  dot2archimate
```

## Environment Variables

You can configure the application with environment variables:

```bash
docker run -p 5000:5000 -e SECRET_KEY=your_secure_key dot2archimate
```

Available environment variables:

- `SECRET_KEY`: Secret key for Flask session security (default: dev_key_for_flash_messages)
- `DEBUG`: Set to True for debug mode (default: False in Docker)
- `LOG_LEVEL`: Set logging level (default: INFO)

For Docker Compose, you can use a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit the file with your values
nano .env

# Use the .env file by uncommenting the env_file section in docker-compose.yml
```

## Using Docker Compose

A `docker-compose.yml` file is provided for convenience:

```bash
# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

## Legal Settings

The Docker container includes a template for legal settings. To configure:

1. The template is automatically copied to the container on first run
2. You can modify it using the CLI:

   ```bash
   docker run -it -v $(pwd)/config:/app/dot2archimate/web/config \
     dot2archimate legal-config --company-name "Your Company" --email "contact@example.com"
   ```

3. Or you can manually edit the file:

   ```bash
   # Copy the template if you haven't already
   cp dot2archimate/web/config/legal_settings.yml.template dot2archimate/web/config/legal_settings.yaml
   
   # Edit the file
   nano dot2archimate/web/config/legal_settings.yaml
   ```

## Production Deployment

For production deployment:

1. Create a proper `.env` file with secure values
2. Use a reverse proxy (Nginx, Traefik) for HTTPS
3. Consider using Docker Swarm or Kubernetes for orchestration

Example production docker-compose.yml:

```yaml
version: '3'

services:
  dot2archimate:
    image: dot2archimate
    ports:
      - "5000:5000"
    volumes:
      - ./examples:/app/examples
      - ./output:/app/output
      - ./config:/app/dot2archimate/web/config
    environment:
      - SECRET_KEY=${SECRET_KEY}
    restart: always
    networks:
      - proxy-network

networks:
  proxy-network:
    external: true
```

## Troubleshooting

Common issues:

1. **Permission issues**: Ensure the volumes have appropriate permissions
2. **Port conflicts**: Change the port mapping if 5000 is already in use
3. **Missing files**: Verify that paths are correct when mounting volumes 