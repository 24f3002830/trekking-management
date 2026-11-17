"""
Celery Application Configuration for Trekking Management Application (TMA).
Configures Redis broker, result backend, and Celery Beat periodic schedules for:
1. Daily Reminders (Upcoming treks notification to users)
2. Monthly Activity Report (Admin monthly statistics HTML report)
"""

import os
import sys
from celery import Celery
from celery.schedules import crontab

# Ensure project root is in python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Redis Broker & Backend URLs
REDIS_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
REDIS_BACKEND_URL = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')

celery = Celery(
    'trekking_tasks',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BACKEND_URL,
    include=['backend.tasks']
)

celery.conf.update(
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,  # 1 hour
    broker_connection_retry_on_startup=False,
    broker_transport_options={
        'visibility_timeout': 3600,
        'socket_connect_timeout': 1,
        'socket_timeout': 1,
    },
    # Periodic Beat Schedule
    beat_schedule={
        # Scheduled Job 1: Daily Reminders (Every day at 08:00 AM)
        'daily-reminders-job': {
            'task': 'backend.tasks.send_daily_reminders',
            'schedule': crontab(hour=8, minute=0),
        },
        # Scheduled Job 2: Monthly Activity Report (1st of every month at midnight)
        'monthly-activity-report-job': {
            'task': 'backend.tasks.generate_monthly_activity_report',
            'schedule': crontab(day_of_month=1, hour=0, minute=0),
        },
    }
)

if __name__ == '__main__':
    celery.start()
