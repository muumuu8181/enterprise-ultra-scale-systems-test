class ScramSystem:
    """
    Manages the emergency shutdown (SCRAM) system.
    """
    def __init__(self):
        self.scram_active = False
        self.scram_reason = None

    def evaluate_monitors(self, monitor_status: dict[str, bool]):
        """
        Evaluates the status from various process monitors.
        If any monitor reports a danger condition (True), SCRAM is initiated.

        Args:
            monitor_status (dict): A dictionary mapping monitor names to their trip status.
                                   e.g., {"CoreTemp": True, "Pressure": False}
        """
        for monitor_name, is_tripped in monitor_status.items():
            if is_tripped:
                self.initiate_scram(reason=f"Trip signal from {monitor_name}")
                return

    def initiate_scram(self, reason: str = "Unknown"):
        """
        Activates the SCRAM mechanism (simulated).
        """
        if not self.scram_active:
            print(f"!!! SCRAM INITIATED !!! Reason: {reason}")
            print(">>> Control Rods Inserting...")
            print(">>> Reactor Shutdown Sequence Active.")
            self.scram_active = True
            self.scram_reason = reason

    def reset(self):
        """
        Resets the SCRAM system (requires manual intervention in real life).
        """
        print("SCRAM System Reset - Control Rods Withdrawn.")
        self.scram_active = False
        self.scram_reason = None
