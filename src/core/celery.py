"""
Celery configuration for AAQIS project.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')

app = Celery('aaqis')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks schedule
app.conf.beat_schedule = {
    'fetch-aqicn-data-hourly': {
        'task': 'src.application.tasks.data_collection.fetch_aqicn_data',
        'schedule': 3600.0,  # Every hour
    },
}
