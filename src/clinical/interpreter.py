class ClinicalInterpreter:
    def __init__(self):
        pass

    def interpret(self, annotation_data):
        """
        Determines the clinical significance of a variant based on annotation data.

        Args:
            annotation_data (dict): Dictionary containing variant annotations.

        Returns:
            str: Clinical interpretation status (e.g., 'ACTIONABLE', 'BENIGN', 'UNCERTAIN').
        """
        if not annotation_data:
            return "UNKNOWN"

        pathogenicity = annotation_data.get("pathogenicity", "").lower()

        if "pathogenic" in pathogenicity:
            return "ACTIONABLE"
        elif "benign" in pathogenicity:
            return "BENIGN"
        else:
            return "UNCERTAIN"
