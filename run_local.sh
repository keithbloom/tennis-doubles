#!/bin/bash

# Build the Docker image
docker build -t tennis-tournament-app .

# Run the container
docker run -p 8000:8000 \
  -v "$(pwd)/local_data:/code/data" \
  -e SQLITE_DB_PATH=/code/data/local_db.sqlite3 \
  tennis-tournament-app