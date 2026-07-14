FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements_enhanced.txt .
RUN pip install --no-cache-dir -r requirements_enhanced.txt

# Copy application
COPY deepseek_python_20260707_a6bd19.py .
COPY lhm_enhanced.py .
COPY stealth_scraper.py .
COPY start_engine.py .

# Create data directory
RUN mkdir -p data logs models

# Run the engine
CMD ["python", "deepseek_python_20260707_a6bd19.py", "--dry-run"]
