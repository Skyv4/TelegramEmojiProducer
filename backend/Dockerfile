# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install uv (a fast package installer)
RUN pip install uv

# Copy pyproject.toml and uv.lock, then install dependencies
COPY pyproject.toml .
COPY requirements.txt .
COPY uv.lock .
RUN uv sync

# Copy the rest of the application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to run the application (specified in docker-compose.yml)
# CMD ["uvicorn", "telegramemojis.main:app", "--host", "0.0.0.0", "--port", "8000"]
