from sqlalchemy import Integer, String, Float, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base
import enum

class SpaceType(str, enum.Enum):
    room = "room"
    world = "world"
    event = "event"

class AssetType(str, enum.Enum):
    model_3d = "3d_model"
    texture = "texture"
    audio = "audio"

class VirtualSpace(Base):
    __tablename__ = "virtual_spaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    owner_id: Mapped[int] = mapped_column(Integer)
    max_occupancy: Mapped[int] = mapped_column(Integer, default=100)
    current_users: Mapped[int] = mapped_column(Integer, default=0)
    space_type: Mapped[SpaceType] = mapped_column(SAEnum(SpaceType), default=SpaceType.room)
    asset_manifest: Mapped[dict] = mapped_column(JSON, default={})

class Avatar(Base):
    __tablename__ = "avatars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    appearance: Mapped[dict] = mapped_column(JSON, default={})
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)
    current_space_id: Mapped[int] = mapped_column(Integer, ForeignKey("virtual_spaces.id"), nullable=True)

class VirtualAsset(Base):
    __tablename__ = "virtual_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    asset_type: Mapped[AssetType] = mapped_column(SAEnum(AssetType))
    file_cid: Mapped[str] = mapped_column(String)
    creator_id: Mapped[int] = mapped_column(Integer)
    price_tokens: Mapped[int] = mapped_column(Integer, default=0)
    # Using asset_metadata to avoid conflict with SQLAlchemy Base.metadata
    asset_metadata: Mapped[dict] = mapped_column("metadata", JSON, default={})
