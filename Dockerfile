# Slim Python base — smaller attack surface, smaller image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first — Docker caches this layer
# so pip only re-runs when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

# Expose the port uvicorn runs on
EXPOSE 8000

# Run with uvicorn — no --reload in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]