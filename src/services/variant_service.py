from typing import List
from src.models.genomics_models import VariantResponse, GenomicReport, SampleStatus

# Mock data
MOCK_VARIANTS = [
    {
        "id": 1,
        "sample_id": 1,
        "chromosome": "chr1",
        "position": 12345,
        "ref_allele": "A",
        "alt_allele": "T",
        "gene": "BRCA1",
        "consequence": "missense_variant",
        "clinvar_significance": "pathogenic"
    },
    {
        "id": 2,
        "sample_id": 1,
        "chromosome": "chr2",
        "position": 67890,
        "ref_allele": "G",
        "alt_allele": "C",
        "gene": "TP53",
        "consequence": "frameshift_variant",
        "clinvar_significance": "likely_pathogenic"
    }
]

async def annotate_variants(sample_id: int) -> List[VariantResponse]:
    # In a real service, this would call an annotation pipeline or query DB
    variants = [v for v in MOCK_VARIANTS if v["sample_id"] == sample_id]
    return [VariantResponse(**v) for v in variants]

async def classify_pathogenicity(variant_id: int) -> str:
    # Mock classification logic
    for v in MOCK_VARIANTS:
        if v["id"] == variant_id:
            return v["clinvar_significance"]
    return "unknown"

async def generate_clinical_report(sample_id: int) -> GenomicReport:
    # Mock report generation
    variants = await annotate_variants(sample_id)

    summary = f"Found {len(variants)} variants for sample {sample_id}."

    report = GenomicReport(
        sample_id=sample_id,
        patient_id="patient_123", # Mock patient ID
        status=SampleStatus.completed,
        variants=variants,
        summary=summary
    )
    return report
