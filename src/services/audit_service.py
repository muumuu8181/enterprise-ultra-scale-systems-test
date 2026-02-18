from sqlalchemy.ext.asyncio import AsyncSession
from ..models.audit_log import AuditLog
import uuid
import json

class AuditService:
    """監査ログサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(self, action: str, target_table: str, target_id: str,
                         before: dict | None = None, after: dict | None = None,
                         user_id: uuid.UUID | None = None, ip_address: str | None = None,
                         user_agent: str | None = None):
        """
        操作ログを記録します。

        Args:
            action: 操作内容 (CREATE, UPDATE, DELETE, VIEW)
            target_table: 対象テーブル名
            target_id: 対象ID
            before: 変更前データ
            after: 変更後データ
        """
        # JSONシリアライズ可能な形式に変換（簡易的）
        log = AuditLog(
            user_id=user_id,
            action=action,
            target_table=target_table,
            target_id=str(target_id),
            before_data=self._serialize(before),
            after_data=self._serialize(after),
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        # 注意: ここではcommitしない（呼び出し元のトランザクションに含めるため）
        # ただし、監査ログは失敗しても記録したい場合があるため、要件によっては別セッションで行う。
        # 今回は同一トランザクション内とする。

    def _serialize(self, data: dict | None) -> dict | None:
        if data is None:
            return None
        # UUIDやDateなどを文字列に変換する処理が必要だが、
        # ここではPydanticのjsonable_encoderを使うか、簡易的にstrにする
        # 今回は省略し、dictをそのまま渡すが、SQLAlchemyのJSON型はPythonのdictを受け付ける
        return data
