# Use the official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install poetry

# Copy the pyproject.toml and poetry.lock files from the parent directory
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install

# Copy the rest of the application code
COPY . .


# Expose port 8000
EXPOSE 8000

# Command to run the Django application
CMD ["poetry", "run", "python", "manage.py", "makemigrations", "&&", "poetry", "run", "python", "manage.py", "migrate", "&&", "poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
