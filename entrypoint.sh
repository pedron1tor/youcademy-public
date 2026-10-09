#!/bin/bash
set -e

if [ "$1" = 'run_server' ]; then
    echo "Starting the server..."
    daphne -b 0.0.0.0 -p $PORT mainframe.asgi:application
elif [ "$1" = 'migrate' ]; then
    echo "Collecting static files..."
    python manage.py migrate
    python manage.py collectstatic --noinput --clear
else
    echo "Running custom command: $@"
    exec "$@"
fi