import os
from celery import celery
from wxml import settings

app = Celery('wxml')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.taks(bind=True)
def debug_task(self):
    print("Request: {0!r".format(self.request))