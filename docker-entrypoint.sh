#!/bin/sh
set -e

python manage.py migrate --noinput

python manage.py ensure_user

if [ "${SEED_DATA:-false}" = "true" ]; then
    python manage.py seed_defaults
fi

exec "$@"
