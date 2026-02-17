from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class EdgeNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    location: str
    region: str
    ip_address: str
    capacity_gbps: float
    active_connections: int
    cache_hit_rate: float

class ContentManifest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_id: str
    format: str = Field(..., description="hls, dash, or mp4")
    resolutions: Dict[str, Any]  # JSON structure for resolutions
    drm_protected: bool
    storage_path: str

class CacheRule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_type: str
    ttl_seconds: int
    priority: int
    edge_nodes: List[str]  # JSON list of edge node IDs

class Rendition(BaseModel):
    resolution: str
    bitrate: int
    codec: str = "h264"

class PushResult(BaseModel):
    success: bool
    content_id: str
    regions_pushed: List[str]
    timestamp: str
