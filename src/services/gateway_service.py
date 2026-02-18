from typing import Dict, Any, Optional
import time
import asyncio

class Response:
    def __init__(self, status_code: int, content: bytes, headers: Dict[str, str]):
        self.status_code = status_code
        self.content = content
        self.headers = headers

class UsageRecord:
    def __init__(self, subscription_id: int, endpoint: str, response_ms: float, timestamp: float):
        self.subscription_id = subscription_id
        self.endpoint = endpoint
        self.response_ms = response_ms
        self.timestamp = timestamp

async def proxy_request(
    subscription_id: int,
    path: str,
    method: str,
    headers: Dict[str, str],
    body: Optional[bytes] = None
) -> Response:
    """
    Proxies the request to the upstream service.
    In a real implementation, this would look up the base URL for the product associated with the subscription
    and forward the request.
    """
    # Mock implementation: just simulate a delay and return a dummy response
    await asyncio.sleep(0.1) # Simulate network latency

    return Response(
        status_code=200,
        content=b'{"message": "Proxy successful"}',
        headers={"Content-Type": "application/json"}
    )

async def enforce_rate_limit(api_key: str) -> bool:
    """
    Checks if the API key has exceeded its rate limit.
    """
    # Mock implementation: always allow
    return True

async def track_usage(
    subscription_id: int,
    endpoint: str,
    response_ms: float
) -> UsageRecord:
    """
    Records the usage for a subscription.
    """
    # Mock implementation
    return UsageRecord(
        subscription_id=subscription_id,
        endpoint=endpoint,
        response_ms=response_ms,
        timestamp=time.time()
    )
