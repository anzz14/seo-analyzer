#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is up."

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic -c alembic.ini upgrade head
else
  echo "Skipping migrations for this container."
fi

echo "Starting application..."
exec "$@"
