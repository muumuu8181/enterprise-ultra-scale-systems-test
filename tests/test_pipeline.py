import unittest
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sequence_processing.fastq_processor import FastqProcessor
from src.annotation.variant_annotator import VariantAnnotator
from src.clinical.interpreter import ClinicalInterpreter

class TestGenomePipeline(unittest.TestCase):

    def setUp(self):
        self.fastq_processor = FastqProcessor()
        self.annotator = VariantAnnotator()
        self.interpreter = ClinicalInterpreter()
        self.test_fastq_path = "test.fastq"

        # Create a dummy FASTQ file
        with open(self.test_fastq_path, "w") as f:
            f.write("@SEQ_ID_1\n")
            f.write("ATGC\n")
            f.write("+\n")
            f.write("IIII\n") # ASCII 73 ('I'). 73-33 = 40 (Quality)

    def tearDown(self):
        if os.path.exists(self.test_fastq_path):
            os.remove(self.test_fastq_path)

    def test_fastq_processing(self):
        reads = list(self.fastq_processor.process_file(self.test_fastq_path))
        self.assertEqual(len(reads), 1)
        read_id, seq, qual, avg_qual = reads[0]
        self.assertEqual(read_id, "SEQ_ID_1")
        self.assertEqual(seq, "ATGC")
        self.assertEqual(avg_qual, 40.0)

    def test_annotation_logic(self):
        # Test a known pathogenic variant from the mock DB
        # ("chr17", 41245, "C", "G") -> TP53 Pathogenic
        annotation = self.annotator.annotate_variant("chr17", 41245, "C", "G")
        self.assertEqual(annotation["gene"], "TP53")
        self.assertEqual(annotation["pathogenicity"], "Pathogenic")

        # Test a known benign variant
        # ("chr2", 20000, "G", "A") -> Benign
        annotation_benign = self.annotator.annotate_variant("chr2", 20000, "G", "A")
        self.assertEqual(annotation_benign["pathogenicity"], "Benign")

        # Test unknown variant
        annotation_unknown = self.annotator.annotate_variant("chrX", 123, "A", "T")
        self.assertEqual(annotation_unknown, {})

    def test_clinical_interpretation(self):
        # Case 1: Actionable
        annotation_pathogenic = {"pathogenicity": "Pathogenic", "gene": "BRCA1"}
        result = self.interpreter.interpret(annotation_pathogenic)
        self.assertEqual(result, "ACTIONABLE")

        # Case 2: Benign
        annotation_benign = {"pathogenicity": "Benign", "gene": "TIN"}
        result = self.interpreter.interpret(annotation_benign)
        self.assertEqual(result, "BENIGN")

        # Case 3: Uncertain/Unknown
        annotation_empty = {}
        result = self.interpreter.interpret(annotation_empty)
        self.assertEqual(result, "UNKNOWN")

        annotation_uncertain = {"pathogenicity": "VUS"}
        result = self.interpreter.interpret(annotation_uncertain)
        self.assertEqual(result, "UNCERTAIN")

    def test_integration_flow(self):
        """
        Simulates the flow:
        1. (Simulated) Variant Calling identifies a variant.
        2. Annotation service annotates it.
        3. Clinical service interprets it.
        """
        # Step 1: Simulated Variant Call (mocking the output of a variant caller)
        variant_call = ("chr1", 10500, "A", "T") # Our mock DB has this as Likely Pathogenic

        # Step 2: Annotation
        annotation = self.annotator.annotate_variant(*variant_call)
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.get("gene"), "OR4F5")

        # Step 3: Interpretation
        clinical_report = self.interpreter.interpret(annotation)

        # Expect "Likely Pathogenic" -> ACTIONABLE
        self.assertEqual(clinical_report, "ACTIONABLE")

if __name__ == '__main__':
    unittest.main()
