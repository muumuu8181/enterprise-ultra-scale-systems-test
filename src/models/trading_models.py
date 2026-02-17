from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class AccountType(str, Enum):
    CASH = "cash"
    MARGIN = "margin"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"

class TradingAccount(BaseModel):
    id: str
    user_id: str
    account_type: AccountType
    balance: float
    buying_power: float
    portfolio_value: float
    day_trades_used: int = 0

class Order(BaseModel):
    id: str
    account_id: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: int
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_at: Optional[datetime] = None

class Position(BaseModel):
    id: str
    account_id: str
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float

class OrderResult(BaseModel):
    success: bool
    message: str
    order: Optional[Order] = None
