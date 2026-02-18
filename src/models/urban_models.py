from sqlalchemy import String, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from src.db.base import Base
import enum

class DevelopmentStatus(str, enum.Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"

class ProjectType(str, enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED = "mixed"

class UrbanZone(Base):
    __tablename__ = "urban_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    zone_type: Mapped[str] = mapped_column(String)
    population_density: Mapped[float] = mapped_column(Float)
    avg_income: Mapped[float] = mapped_column(Float)
    infrastructure_score: Mapped[float] = mapped_column(Float)

class LandParcel(Base):
    __tablename__ = "land_parcels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parcel_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    zoning_code: Mapped[str] = mapped_column(String)
    area_sqm: Mapped[float] = mapped_column(Float)
    current_use: Mapped[str] = mapped_column(String)
    allowed_uses: Mapped[list] = mapped_column(JSON)

    # Using Geometry type. Assuming POLYGON for parcels.
    # Note: SQLite/Spatialite requires correct loading.
    geometry = mapped_column(Geometry("POLYGON", srid=4326))

class DevelopmentProject(Base):
    __tablename__ = "development_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parcel_id: Mapped[str] = mapped_column(String, ForeignKey("land_parcels.parcel_id"))
    project_type: Mapped[str] = mapped_column(String) # Storing enum as string
    units: Mapped[int] = mapped_column(Integer)
    floors: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="proposed")

    parcel: Mapped["LandParcel"] = relationship("LandParcel")
