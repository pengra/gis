import os
from celery import Celery
from wxml import settings

app = Celery('wxml')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wxml.settings')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r".format(self.request))
