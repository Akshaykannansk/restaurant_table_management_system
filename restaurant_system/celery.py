import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_system.settings')

app = Celery('restaurant_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-pending-bills-every-minute': {
        'task': 'core.tasks.check_pending_bills',
        'schedule': crontab(minute='*'), # Run every minute
    },
    'auto-close-abandoned-tables-every-hour': {
        'task': 'core.tasks.auto_close_abandoned_tables',
        'schedule': crontab(minute=0, hour='*'), # Run at minute 0 of every hour
    },
}
