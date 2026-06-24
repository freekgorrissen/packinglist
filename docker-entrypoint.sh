#!/bin/sh
set -e

python manage.py migrate --noinput

if [ "${SEED_DATA:-false}" = "true" ]; then
    python manage.py seed_defaults
fi

exec "$@"
