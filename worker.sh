. secrets.sh
cd $SERVER_LOCATION
source ".env/bin/activate"
cd "src"
celery -A worker -c 6 -l info