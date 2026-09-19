FROM python:3.11-slim

ARG APP_CONTEXT=.

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the configured build context. This supports both:
# - docker build -f backend/Dockerfile backend
# - docker build -f backend/Dockerfile --build-arg APP_CONTEXT=backend .
COPY ${APP_CONTEXT}/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application source from the selected build context
COPY ${APP_CONTEXT} .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from urllib.request import urlopen; response = urlopen('http://localhost:8000/health'); exit(0 if response.status == 200 else 1)"

# Run application
CMD ["python", "main.py"]
