import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.economy_service import EconomyService
from src.models.nft_models import VirtualLand

class Avatar:
    """
    テスト用アバタークラス (シミュレーション)
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    # executeの戻り値をモック
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result
    return session

@pytest.fixture
def economy_service(mock_db_session):
    return EconomyService(mock_db_session)

@pytest.mark.asyncio
async def test_proximity_detection(economy_service, mock_db_session):
    """
    近接検知のテスト: 指定座標周辺の土地が正しく検索されるか確認
    """
    # ターゲット座標
    target_x, target_y = 10, 10
    radius = 2

    # モックデータの準備
    nearby_land = VirtualLand(parcel_x=11, parcel_y=11, owner_id="neighbor")
    far_land = VirtualLand(parcel_x=20, parcel_y=20, owner_id="far")

    # DBクエリの戻り値を設定 (get_nearby_landsはDBクエリを実行する)
    # ここでは、クエリの中身まで解析してフィルタリングするのは困難なため、
    # サービスが正しくDBを呼び出し、その結果を返すことを確認する。
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [nearby_land]
    mock_db_session.execute.return_value = mock_result

    # テスト実行
    result = await economy_service.get_nearby_lands(target_x, target_y, radius)

    # 検証
    assert len(result) == 1
    assert result[0].owner_id == "neighbor"
    assert mock_db_session.execute.called

    # 呼び出し引数の確認 (範囲クエリが構成されているか)
    # SQLアルケミーのステートメントは複雑なので、呼び出されたこと自体を主眼に置く
    # もしくは、実際のロジックをテストするためにインメモリDBを使うのが理想だが、
    # ここではモックでサービスの振る舞いを確認する。

@pytest.mark.asyncio
async def test_avatar_movement():
    """
    アバター移動のテスト: 座標更新ロジックの確認
    """
    # 初期位置 (0, 0)
    avatar = Avatar(0, 0)

    # (1, 1) へ移動
    avatar.move(1, 1)
    assert avatar.x == 1
    assert avatar.y == 1

    # (-1, 0) へ移動 -> (0, 1)
    avatar.move(-1, 0)
    assert avatar.x == 0
    assert avatar.y == 1

    # 境界チェックなどのロジックがあればここに追加
