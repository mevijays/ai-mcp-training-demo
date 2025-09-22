#!/usr/bin/env bash
set -euo pipefail

# Load env if present
if [ -f .env ]; then
  set -o allexport
  source .env
  set +o allexport
fi

export POSTGRES_USER="${POSTGRES_USER:-demo}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-demo_password}"
export POSTGRES_DB="${POSTGRES_DB:-demodb}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"

if [ "${RUN_MODE:-host}" = "container" ]; then
  : "${POSTGRES_HOST:?}"
  : "${POSTGRES_PORT:?}"
  : "${POSTGRES_USER:?}"
  : "${POSTGRES_PASSWORD:?}"
  : "${POSTGRES_DB:?}"

  export PGPASSWORD="$POSTGRES_PASSWORD"
  until psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" >/dev/null 2>&1; do
    echo "Waiting for Postgres..."
    sleep 2
  done
  psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /scripts/sample.sql
  echo "Sample data applied (container mode)."
else
  # Start DB and init service
  COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose up -d db
  # Run the init one-off container to seed data after db is healthy
  COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose up --abort-on-container-exit --no-deps db-init

  echo "Database ready on port ${POSTGRES_PORT}."
fi
