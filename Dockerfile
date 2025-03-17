FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    DEBUG=False \
    LOG_LEVEL=INFO

# Install Graphviz dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the project
COPY . .

# Install the package
RUN pip install -e .

# Create a non-root user and switch to it
RUN useradd -m dotuser && \
    chown -R dotuser:dotuser /app
USER dotuser

# Create config directory for legal settings
RUN mkdir -p /app/dot2archimate/web/config

# Copy the template file (if it doesn't exist in the image)
RUN cp -n /app/dot2archimate/web/config/legal_settings.yml.template /app/dot2archimate/web/config/legal_settings.yaml || true

# Expose the port
EXPOSE 5000

# Set the entry point
ENTRYPOINT ["dot2archimate"]
CMD ["web", "--host", "0.0.0.0", "--port", "5000"] 