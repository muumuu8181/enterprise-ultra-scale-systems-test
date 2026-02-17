from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.core.security import decode_token, is_token_blacklisted

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT認証ミドルウェア
    Bearerトークンを検証し、顧客IDをrequest.stateに注入します。
    """
    def __init__(self, app, exclude_paths: list[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next):
        # 除外パスの判定（完全一致または正規表現などが考えられるが、ここでは単純な前方一致やリスト確認）
        # ドキュメント関連やログイン・リフレッシュエンドポイントは除外
        path = request.url.path
        if any(path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "認証情報が不足しているか、無効です。"}
            )

        token = auth_header.split(" ")[1]

        # ブラックリスト確認
        if await is_token_blacklisted(token):
             return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "トークンが無効化されています。"}
            )

        # トークン検証
        payload = decode_token(token)
        if payload is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "トークンが無効か、期限切れです。"}
            )

        # トークンタイプの確認（access tokenのみ許可するなど）
        if payload.get("type") != "access":
             return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "アクセストークンが必要です。"}
            )

        # 顧客IDをstateに注入
        request.state.customer_id = payload.get("sub")
        request.state.token = token # ログアウト時などに利用可能

        return await call_next(request)
