from sqlalchemy import Column, Integer, String, JSON, Float
from src.database import Base

class PharmacogenomicProfile(Base):
    __tablename__ = "pharmacogenomic_profiles"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    cyp2d6_phenotype = Column(String)
    cyp2c19_phenotype = Column(String)
    drug_recommendations = Column(JSON)

class PopulationStudy(Base):
    __tablename__ = "population_studies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    cohort_size = Column(Integer)
    variants_analyzed = Column(Integer)
    associations = Column(JSON)
    publication_doi = Column(String)

class PanelDesign(Base):
    __tablename__ = "panel_designs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    genes = Column(JSON)
    disease_indication = Column(String)
    coverage_target_pct = Column(Float)
    bait_set_uri = Column(String)
