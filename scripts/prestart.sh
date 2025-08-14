#!/usr/bin/env bash

set -euo pipefail
set -x

# Let the DB start
python scripts/backend_prestart.py

# Run migrations
alembic upgrade head

# Create OpenFGA stores
python scripts/init_openfga.py

# Apply OpenFGA model migrations if available
fga model test --tests "$OPENFGA_TESTS_STORE_FILE"
bash scripts/openfga_model_migrations.sh "$FGA_STORE_NAME" "$OPENFGA_STORE_FILE"

# Create initial data in DB
python scripts/initial_data.py
