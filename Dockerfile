# Jawak backend image.
# Django 6.0 requires Python 3.12+.
FROM python:3.12-slim

# - Don't write .pyc files; stream stdout/stderr straight to the console.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
# psycopg2-binary and Pillow ship prebuilt wheels, so no system build deps
# are required.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project.
COPY . .

# Run as an unprivileged user so a compromised process isn't root inside the
# container. Give it ownership of the app dir for any runtime writes.
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# Dev server. For production, run gunicorn against config.wsgi:application
# with DJANGO_SETTINGS_MODULE=config.settings.production.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
