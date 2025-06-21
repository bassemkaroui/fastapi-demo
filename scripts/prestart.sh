#!/usr/bin/env bash

set -e
set -x

# Let the DB start
python scripts/backend_prestart.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python scripts/initial_data.py
