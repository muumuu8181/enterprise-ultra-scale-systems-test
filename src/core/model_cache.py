import logging
import sys
from collections import OrderedDict
from typing import Optional, Any

# PyTorchのインポートを試みる（GPUチェック用）
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

logger = logging.getLogger(__name__)

class ModelCache:
    """
    モデルキャッシュ管理クラス
    LRU (Least Recently Used) ポリシーによるキャッシュエビクション、
    メモリ使用量の追跡、GPU可用性チェックを行います。
    """

    def __init__(self, capacity: int = 10):
        """
        初期化
        Args:
            capacity (int): 最大キャッシュ数
        """
        self._cache: OrderedDict[int, Any] = OrderedDict()
        self._capacity: int = capacity

    def get(self, model_id: int) -> Optional[Any]:
        """
        モデルをキャッシュから取得します。
        アクセスされたモデルはLRUの最後に移動されます。
        """
        if model_id not in self._cache:
            return None
        self._cache.move_to_end(model_id)
        return self._cache[model_id]

    def put(self, model_id: int, model: Any) -> None:
        """
        モデルをキャッシュに追加します。
        容量を超えた場合は最も古いエントリを削除します。
        """
        if model_id in self._cache:
            self._cache.move_to_end(model_id)

        self._cache[model_id] = model

        if len(self._cache) > self._capacity:
            self.evict()

    def evict(self) -> None:
        """
        最も古いエントリをキャッシュから削除します。
        """
        if self._cache:
            model_id, _ = self._cache.popitem(last=False)
            logger.info(f"キャッシュからモデル {model_id} を削除しました (LRU)")

    def remove(self, model_id: int) -> bool:
        """
        指定されたモデルをキャッシュから削除します。
        """
        if model_id in self._cache:
            del self._cache[model_id]
            logger.info(f"モデル {model_id} をキャッシュから削除しました (手動)")
            return True
        return False

    def get_memory_usage(self) -> int:
        """
        現在のキャッシュ内モデルのメモリ使用量（バイト）を推定します。
        ※sys.getsizeofによる簡易的な計測です。
        """
        total_size = 0
        for _, model in self._cache.items():
            try:
                total_size += sys.getsizeof(model)
            except Exception:
                pass
        return total_size

    def is_gpu_available(self) -> bool:
        """
        GPUが利用可能かどうかを確認します。
        """
        if HAS_TORCH:
            return torch.cuda.is_available()
        return False
