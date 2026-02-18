import structlog
from src.core.celery_app import celery_app
from src.services.notification_service import NotificationService
from datetime import datetime

logger = structlog.get_logger()

@celery_app.task(name="process_batch_transfer")
def process_batch_transfer():
    """
    Processes batch transfers.
    Scheduled daily at 9:00 AM.
    """
    logger.info("process_batch_transfer_started")
    # Simulate batch processing
    logger.info("process_batch_transfer_completed", processed_count=100)
    return "Batch transfer processed successfully"

@celery_app.task(name="send_notification")
def send_notification(notification_type: str, payload: dict):
    """
    Sends a notification asynchronously.
    """
    logger.info("send_notification_task_received", type=notification_type)

    if notification_type == "transaction_alert":
        NotificationService.send_transaction_alert(
            user_id=payload.get("user_id"),
            amount=payload.get("amount"),
            transaction_type=payload.get("transaction_type")
        )
    elif notification_type == "login_alert":
        NotificationService.send_login_alert(
            user_id=payload.get("user_id"),
            device_info=payload.get("device_info")
        )
    elif notification_type == "fraud_alert":
        NotificationService.send_fraud_alert(
            user_id=payload.get("user_id"),
            reason=payload.get("reason")
        )
    elif notification_type == "statement_ready":
        NotificationService.send_statement_ready(
            user_id=payload.get("user_id"),
            month=payload.get("month")
        )
    else:
        logger.warning("unknown_notification_type", type=notification_type)

@celery_app.task(name="generate_monthly_statement")
def generate_monthly_statement():
    """
    Generates monthly statements for all users.
    Scheduled on the 1st of every month.
    """
    logger.info("generate_monthly_statement_started")
    # Simulate statement generation for users
    # For demo purposes, we'll send a notification for a dummy user
    dummy_user_id = 1
    current_month = datetime.now().strftime("%Y-%m")

    NotificationService.send_statement_ready(dummy_user_id, current_month)
    logger.info("generate_monthly_statement_completed")
    return "Monthly statements generated"
