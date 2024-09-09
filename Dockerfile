ARG PYTHON_VERSION=3.10-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

ENV SECRET_KEY "sQDKqfTUB1tpIEH9g6BOhrY2aKL6vCwatFWTh8gDNVrIDeJULC"
RUN python manage.py collectstatic --noinput

# Create a directory for the SQLite database
RUN mkdir -p /code/data

# Use an environment variable to specify the SQLite database path
ENV SQLITE_DB_PATH=/code/data/db.sqlite3

EXPOSE 8000
RUN python -c "import sys; print(sys.path)"
RUN python -c "import tennis_doubles; print(tennis_doubles.__file__)"
CMD ["gunicorn","--bind",":8000","--workers","2","tennis_doubles.wsgi:application"]
