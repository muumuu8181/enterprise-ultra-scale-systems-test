import logging
from src.models.workzone_models import WorkZone

logger = logging.getLogger(__name__)

class WorkZoneBroadcaster:
    """
    Service for broadcasting Work Zone information via V2X (DENM) and updating HD Maps.
    """

    def generate_denm_message(self, work_zone: WorkZone) -> dict:
        """
        Generates an ETSI ITS DENM message for the work zone.

        Args:
            work_zone (WorkZone): The work zone object.

        Returns:
            dict: The DENM message payload (mocked).
        """
        # In a real implementation, this would construct an ASN.1 UPER encoded message.
        # Here we return a JSON-compatible dictionary.

        # Calculate validity duration
        duration = 3600 # Default 1 hour
        if work_zone.end_date and work_zone.start_date:
            delta = work_zone.end_date - work_zone.start_date
            duration = int(delta.total_seconds())

        denm = {
            "origin_station_id": 9999, # Infrastructure ID
            "cause_code": 3, # Roadworks
            "sub_cause_code": 0,
            "location": str(work_zone.location), # WKT or similar
            "validity_duration": duration,
            "event_info": {
                "closed_lanes": work_zone.closed_lanes,
                "speed_limit": work_zone.speed_limit
            }
        }
        return denm

    async def broadcast_to_rsus(self, denm_message: dict):
        """
        Broadcasts the DENM message to relevant Road Side Units (RSUs).

        Args:
            denm_message (dict): The DENM message to broadcast.
        """
        # Mock broadcasting
        # logger.info(f"Broadcasting DENM to RSUs: {denm_message}")
        print(f"Broadcasting DENM to RSUs: {denm_message}")
        pass

    async def update_hd_map(self, work_zone: WorkZone):
        """
        Updates the HD Map with the new work zone information.

        Args:
            work_zone (WorkZone): The work zone object.
        """
        # Mock HD Map update
        # logger.info(f"Updating HD Map for Work Zone ID {work_zone.id}")
        print(f"Updating HD Map for Work Zone ID {work_zone.id}")
        pass
