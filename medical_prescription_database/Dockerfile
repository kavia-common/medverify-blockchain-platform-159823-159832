# Simple runtime for SQLite DB initialization + health server
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy project files
COPY . /app

# Expose health server port
EXPOSE 5001

# Default environment (can be overridden)
ENV HEALTH_PORT=5001

# Run the startup script which will run migrations and then start the health server
CMD ["python", "start.py"]
