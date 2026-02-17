import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from src.services.fraud_detection import FraudDetectionEngine, TransactionContext
from src.core.event_sourcing import EventModel

@pytest.fixture
def mock_session():
    session = AsyncMock()
    # デフォルトでは空リストを返すように設定 (過去の取引なし、新規受取人なし)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result
    return session

@pytest.fixture
def engine(mock_session):
    return FraudDetectionEngine(mock_session)

@pytest.fixture
def base_context():
    return TransactionContext(
        transaction_id="tx-123",
        source_account_id="acc-A",
        destination_account_id="acc-B",
        amount=10000.0,
        timestamp=datetime(2023, 10, 27, 10, 0, 0) # 10:00 AM (safe time)
    )

@pytest.mark.asyncio
async def test_normal_transaction_passes(engine, base_context, mock_session):
    """正常な取引はスコアが低いこと"""
    # 過去の取引履歴も適当にあるとする (新規ではない)
    # _is_new_recipient が False を返すようにモック調整
    # EventModel(payload={"to_account_id": "acc-B"}) を返す
    mock_event = MagicMock(spec=EventModel)
    mock_event.payload = {"to_account_id": "acc-B"}

    # executeの結果を上書き
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_event] # 1件ヒット=既存
    mock_session.execute.return_value = mock_result

    score = await engine.analyze_transaction(base_context)
    assert score < 50
    assert score == 0 # 他の条件に引っかからなければ0

@pytest.mark.asyncio
async def test_late_night_transaction_flagged(engine, base_context):
    """深夜取引(23-5時)はフラグが立つこと"""
    # 03:00 AM
    context = base_context.model_copy(update={"timestamp": datetime(2023, 10, 27, 3, 0, 0)})

    score = await engine.analyze_transaction(context)
    # 深夜(+30) + 新規受取人(+20, mock default is empty list -> new) = 50
    # Wait, default mock returns empty list for history checks.
    # Empty list for _is_new_recipient means "True" (New).
    # So score will be 30 + 20 = 50.
    assert score >= 30

@pytest.mark.asyncio
async def test_large_amount_requires_review(engine, base_context):
    """高額取引はスコアが高いこと"""
    # 100万円
    context = base_context.model_copy(update={"amount": 1_000_000.0})

    score = await engine.analyze_transaction(context)
    # 高額(+40) + 新規(+20) = 60
    assert score >= 40

@pytest.mark.asyncio
async def test_rapid_successive_transactions_blocked(engine, base_context, mock_session):
    """短時間での連続取引はブロックされること"""
    # _count_recent_transactions が 3 を返すようにモック
    # _is_new_recipient は True (空リスト) -> +20

    # executeの呼び出し順序によって戻り値を制御するのは難しいので、
    # 副作用(side_effect)を使うか、緩いチェックにする。
    # ここでは単純に全てのリクエストに対して「3件の履歴あり」かつ「新規ではない(履歴あり)」を返すようにしてみる
    # しかし _is_new_recipient と _count_recent_transactions は別のクエリ。

    # 簡易的に、どのようなクエリでもリスト[ev1, ev2, ev3]を返すようにする。
    # _count_recent_transactions -> len=3 -> +50
    # _is_new_recipient -> loop checks payload -> if "acc-B" found -> False(Old).

    mock_event = MagicMock(spec=EventModel)
    mock_event.payload = {"to_account_id": "acc-B"}

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_event, mock_event, mock_event]
    mock_session.execute.return_value = mock_result

    # 期待値:
    # Rapid(+50)
    # NewRecipient? -> リスト内に "acc-B" があるので False -> +0
    # Total = 50.

    # Wait, I want to test "Blocked". Block happens at >= 90.
    # To get >= 90, I need more flags.
    # Let's add High Amount (+40).
    # Total = 50 + 40 = 90 -> Blocked.

    context = base_context.model_copy(update={"amount": 1_000_000.0})

    # block_suspicious_transaction raises ValueError
    with pytest.raises(ValueError) as excinfo:
        await engine.analyze_transaction(context)

    assert "blocked" in str(excinfo.value)

@pytest.mark.asyncio
async def test_new_recipient_flagged(engine, base_context, mock_session):
    """新しい送金先はフラグが立つこと"""
    # モックはデフォルトで空リストを返す -> 新規と判定される
    score = await engine.analyze_transaction(base_context)
    # 新規(+20)
    assert score >= 20
