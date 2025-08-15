FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    postgresql-client \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Install 2QC+ in development mode
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash qc2plus && \
    chown -R qc2plus:qc2plus /app

USER qc2plus

# Set environment variables
ENV PYTHONPATH=/app
ENV QC2PLUS_HOME=/app

# Expose port for potential web interface
EXPOSE 8080

# Default command
CMD ["qc2plus", "--help"]
