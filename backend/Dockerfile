FROM python:3.10-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers for HU provider
RUN playwright install --with-deps chromium

# Copy app code
COPY app ./app

# Expose port
EXPOSE 8000

# Default start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
