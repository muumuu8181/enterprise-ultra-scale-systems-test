import structlog
from typing import Dict, Any

logger = structlog.get_logger()

class NotificationService:
    @staticmethod
    def send_transaction_alert(user_id: int, amount: float, transaction_type: str) -> None:
        """
        Sends an alert for a transaction (Email + SMS).
        """
        logger.info(
            "sending_transaction_alert",
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            channels=["email", "sms"]
        )
        # Simulation of sending email and SMS
        print(f"Transaction Alert for User {user_id}: {transaction_type} of {amount}")

    @staticmethod
    def send_login_alert(user_id: int, device_info: Dict[str, Any]) -> None:
        """
        Sends an alert for a new device login.
        """
        logger.info(
            "sending_login_alert",
            user_id=user_id,
            device_info=device_info
        )
        print(f"Login Alert for User {user_id}: New device detected - {device_info}")

    @staticmethod
    def send_fraud_alert(user_id: int, reason: str) -> None:
        """
        Sends an immediate fraud alert.
        """
        logger.warning(
            "sending_fraud_alert",
            user_id=user_id,
            reason=reason,
            priority="high"
        )
        print(f"FRAUD ALERT for User {user_id}: {reason}")

    @staticmethod
    def send_statement_ready(user_id: int, month: str) -> None:
        """
        Notifies the user that their monthly statement is ready.
        """
        logger.info(
            "sending_statement_ready",
            user_id=user_id,
            month=month
        )
        print(f"Statement Ready for User {user_id}: Month {month}")
