class VariantAnnotator:
    def __init__(self):
        # Mock database of variants
        # Key: (chromosome, position, ref, alt)
        # Value: {gene, transcript, impact, cadd_score, pathogenicity}
        self.mock_db = {
            ("chr1", 10500, "A", "T"): {
                "gene": "OR4F5",
                "transcript": "NM_001005484",
                "impact": "MODERATE",
                "cadd_score": 25.4,
                "pathogenicity": "Likely Pathogenic"
            },
            ("chr17", 41245, "C", "G"): {
                "gene": "TP53",
                "transcript": "NM_000546",
                "impact": "HIGH",
                "cadd_score": 32.1,
                "pathogenicity": "Pathogenic"
            },
            ("chr2", 20000, "G", "A"): {
                "gene": "TIN",
                "transcript": "NM_001123",
                "impact": "LOW",
                "cadd_score": 10.2,
                "pathogenicity": "Benign"
            }
        }

    def annotate_variant(self, chromosome, position, ref, alt):
        """
        Retrieves annotation for a given variant from the mock database.

        Args:
            chromosome (str): Chromosome name (e.g., 'chr1')
            position (int): Genomic position (1-based)
            ref (str): Reference allele
            alt (str): Alternate allele

        Returns:
            dict: Annotation information or empty dict if not found.
        """
        key = (chromosome, position, ref, alt)
        return self.mock_db.get(key, {})
