FROM python:3.13

# Create and set work directory
WORKDIR /app

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production

# Install dependencies
RUN pip install --upgrade pip

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose port for Gunicorn
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "healthtracker.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
