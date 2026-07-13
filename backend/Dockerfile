FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables to optimize Python for container environments
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Copy requirements file first to utilize Docker layer caching
COPY requirements.txt .

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source directory and files
COPY src/ ./src
COPY README.md .

# Expose port
EXPOSE 8080

# Run Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
