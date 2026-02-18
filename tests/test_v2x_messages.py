import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from src.api.v1.v2x_messages import router as v2x_router
from src.api.v1.pki import router as pki_router
from src.api.v1.ota import router as ota_router
from src.services.glosa_calculator import GLOSACalculator

# テスト用アプリの構築
app = FastAPI()
app.include_router(v2x_router)
app.include_router(pki_router)
app.include_router(ota_router)

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_cam_message_processing(client):
    """
    CAMメッセージ処理のテスト
    """
    payload = {
        "station_id": 123,
        "latitude": 35.6895,
        "longitude": 139.6917,
        "speed": 10.0,
        "heading": 90.0,
        "timestamp": str(datetime.now(timezone.utc))
    }
    response = await client.post("/v2x/cam", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "received"}

@pytest.mark.asyncio
async def test_denm_nearby_query(client):
    """
    DENM周辺検索のテスト
    """
    # アクティブなDENMを取得 (モック)
    response = await client.get("/v2x/denm/active?lat=35.6895&lon=139.6917&radius=500")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_glosa_speed_calculation(client):
    """
    GLOSA推奨速度計算のテスト
    """
    payload = {
        "distance_to_intersection": 300.0,
        "current_speed": 15.0
    }
    response = await client.post("/v2x/glosa/1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "advisory_speed" in data
    assert data["intersection_id"] == 1

def test_glosa_logic():
    """
    GLOSAロジック単体テスト
    """
    calc = GLOSACalculator(max_speed_limit=16.6) # 60km/h

    # 赤信号で残り時間10秒、距離100m -> 10m/sで到達すれば青になる
    speed = calc.calculate_advisory_speed(100.0, 15.0, "RED", 10.0)
    assert abs(speed - 10.0) < 0.1

    # 青信号で残り時間2秒、距離100m -> 50m/s必要 (無理) -> 停止推奨(0.0)
    speed_stop = calc.calculate_advisory_speed(100.0, 15.0, "GREEN", 2.0)
    assert speed_stop == 0.0

@pytest.mark.asyncio
async def test_certificate_rotation(client):
    """
    証明書ローテーションのテスト
    """
    payload = {"vehicle_id": "test-vehicle-001"}
    response = await client.post("/pki/certificates/rotate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == "test-vehicle-001"
    assert "serial_number" in data

@pytest.mark.asyncio
async def test_ota_deployment_flow(client):
    """
    OTAデプロイフローのテスト
    """
    # 1. パッケージ登録
    pkg_payload = {
        "version": "1.0.1",
        "target_ecu": "ivib",
        "checksum": "sha256:xxxx"
    }
    reg_resp = await client.post("/ota/packages", json=pkg_payload)
    assert reg_resp.status_code == 201

    # DBモックのため、以下はAPIの挙動確認のみ

    # 2. 待機中パッケージ確認
    pending_resp = await client.get("/ota/packages/veh001/pending")
    assert pending_resp.status_code == 200

    # 3. デプロイ (ID=1と仮定)
    deploy_resp = await client.post("/ota/packages/1/deploy")
    assert deploy_resp.status_code == 200

    # 4. 進捗確認
    prog_resp = await client.get("/ota/packages/1/progress")
    assert prog_resp.status_code == 200
