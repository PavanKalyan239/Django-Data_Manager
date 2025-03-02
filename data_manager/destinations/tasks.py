# destinations/tasks.py
from celery import shared_task
import requests
from django.utils import timezone
from .models import Log
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_to_destination(log_id):
    log = Log.objects.get(id=log_id)
    destination = log.destination
    try:
        response = requests.request(
            method=destination.http_method,
            url=destination.url,
            headers=destination.headers,
            json=log.received_data
        )
        log.status = 'success' if response.status_code in range(200, 300) else 'failed'
        logger.info(f"Task for log {log_id} completed: Status={log.status}, URL={destination.url}, HTTP Code={response.status_code}")
    except Exception as e:
        log.status = 'failed'
        log.received_data["error_message"] = str(e)
        logger.error(f"Task for log {log_id} failed: {str(e)}")
    log.processed_timestamp = timezone.now()
    log.save()