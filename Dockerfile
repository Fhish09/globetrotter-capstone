# Use an official lightweight Python runtime as the base image
FROM python:3.9-slim

# Set a working directory inside the container
WORKDIR /globetrotter

# Copy dependency file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies + development tools for better reloading
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install watchdog

# Copy the application source code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Default command for development (overridden in docker-compose)
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000", "--debug"]
