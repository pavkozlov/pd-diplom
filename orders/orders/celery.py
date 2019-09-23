import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')

app = Celery('orders')
app.config_from_object('django.conf:settings', )
app.autodiscover_tasks()
