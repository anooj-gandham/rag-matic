# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config', include=['app.tasks.query'])
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# import app.tasks.generate_embeddings
# import app.tasks.query