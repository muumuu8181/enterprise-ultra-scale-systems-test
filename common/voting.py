class VotingSystem:
    """
    Implements voting logic for redundant safety systems.
    """

    def two_out_of_four(self, signals: list[bool]) -> bool:
        """
        Determines if a safety action should be taken based on 2-out-of-4 logic.

        Args:
            signals (list[bool]): A list of 4 boolean signals.
                                  True indicates a trip/danger condition.
                                  False indicates normal operation.

        Returns:
            bool: True if 2 or more signals are True, False otherwise.

        Raises:
            ValueError: If the input list does not contain exactly 4 signals.
        """
        if len(signals) != 4:
            raise ValueError("Voting system requires exactly 4 signals")

        trip_count = sum(signals)
        return trip_count >= 2
