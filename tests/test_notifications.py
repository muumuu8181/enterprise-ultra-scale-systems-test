import pytest
from unittest.mock import patch, MagicMock
from src.services.notification_service import NotificationService
from src.workers.celery_tasks import process_batch_transfer, send_notification, generate_monthly_statement

class TestNotifications:

    @patch('src.services.notification_service.logger')
    def test_send_transaction_alert(self, mock_logger):
        """Test the transaction alert service method."""
        NotificationService.send_transaction_alert(user_id=1, amount=100.0, transaction_type="debit")
        mock_logger.info.assert_called()
        # Verify call args
        args, kwargs = mock_logger.info.call_args
        assert kwargs['user_id'] == 1
        assert kwargs['amount'] == 100.0

    @patch('src.services.notification_service.logger')
    def test_send_fraud_alert(self, mock_logger):
        """Test the fraud alert service method."""
        NotificationService.send_fraud_alert(user_id=1, reason="suspicious location")
        mock_logger.warning.assert_called()
        args, kwargs = mock_logger.warning.call_args
        assert kwargs['user_id'] == 1
        assert kwargs['priority'] == "high"

    @patch('src.workers.celery_tasks.logger')
    def test_process_batch_transfer_task(self, mock_logger):
        """Test the batch transfer processing task."""
        result = process_batch_transfer()
        assert result == "Batch transfer processed successfully"
        # Should verify start and completion logging
        assert mock_logger.info.call_count >= 2

    @patch('src.workers.celery_tasks.NotificationService')
    def test_generate_monthly_statement_task(self, mock_service):
        """Test the monthly statement generation task."""
        result = generate_monthly_statement()
        assert result == "Monthly statements generated"
        # Should verify it calls send_statement_ready
        mock_service.send_statement_ready.assert_called()

    @patch('src.workers.celery_tasks.NotificationService')
    def test_send_notification_dispatch(self, mock_service):
        """Test the send_notification task dispatches to correct service method."""
        payload = {"user_id": 1, "device_info": {"os": "iOS"}}
        send_notification("login_alert", payload)

        mock_service.send_login_alert.assert_called_with(
            user_id=1,
            device_info={"os": "iOS"}
        )
