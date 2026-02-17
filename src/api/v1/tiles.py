from fastapi import APIRouter, Response

router = APIRouter(prefix="/tiles", tags=["tiles"])

@router.get("/{z}/{x}/{y}.pbf")
async def get_vector_tile(z: int, x: int, y: int):
    """
    Serve Mapbox Vector Tiles (MVT).
    Returns a mock binary response for demonstration.
    """
    # In a real system, this would query PostGIS using ST_AsMVT
    # or read from a pre-generated .mbtiles file.

    # Mock empty tile or simple structure
    # This is not a valid PBF but serves as a placeholder for the endpoint contract.
    mock_pbf_data = b'\x1a\x04\x0a\x02\x08\x00'

    return Response(content=mock_pbf_data, media_type="application/x-protobuf")
