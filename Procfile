web: daphne -b 0.0.0.0 -p $PORT mainframe.asgi:application

migrate: python manage.py migrate && python manage.py collectstatic --noinput --clear
createuser: python manage.py createsuperuser --username admin --email admin@example.com --noinput