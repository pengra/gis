. secrets.sh
cd $SERVER_LOCATION
. ".env/bin/activate"
cd "src"
python manage.py collectstatic --no-input
gunicorn --workers=2 -b 127.0.0.1:9996 wxml.wsgi:application
