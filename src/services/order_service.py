from datetime import datetime, timezone
from typing import Dict, List, Optional
from src.models.trading_models import Order, OrderResult, TradingAccount, Position, OrderSide, OrderStatus

# In-memory mock storage
_accounts: Dict[str, TradingAccount] = {}
_orders: Dict[str, Order] = {}
_positions: Dict[str, List[Position]] = {}

async def place_order(account_id: str, order: Order) -> OrderResult:
    # Basic validation
    if order.quantity <= 0:
        return OrderResult(success=False, message="Quantity must be positive")

    # Mock account retrieval/creation
    if account_id not in _accounts:
        _accounts[account_id] = TradingAccount(
            id=account_id,
            user_id="user_123",
            account_type="cash",
            balance=10000.0,
            buying_power=10000.0,
            portfolio_value=10000.0
        )
    account = _accounts[account_id]

    # Calculate estimated cost (using provided price or mock price)
    price = order.price if order.price else 150.0 # Mock market price
    cost = price * order.quantity

    if order.side == OrderSide.BUY:
        if account.buying_power < cost:
            return OrderResult(success=False, message="Insufficient buying power")

        account.buying_power -= cost
        account.balance -= cost

        # Update or create position
        pos_list = _positions.get(account_id, [])
        existing_pos = next((p for p in pos_list if p.symbol == order.symbol), None)

        if existing_pos:
            total_cost = (existing_pos.avg_cost * existing_pos.quantity) + cost
            existing_pos.quantity += order.quantity
            existing_pos.avg_cost = total_cost / existing_pos.quantity
        else:
            new_pos = Position(
                id=f"pos_{account_id}_{order.symbol}",
                account_id=account_id,
                symbol=order.symbol,
                quantity=order.quantity,
                avg_cost=price,
                current_price=price,
                unrealized_pnl=0.0,
                realized_pnl=0.0
            )
            if account_id not in _positions:
                _positions[account_id] = []
            _positions[account_id].append(new_pos)

    elif order.side == OrderSide.SELL:
        pos_list = _positions.get(account_id, [])
        existing_pos = next((p for p in pos_list if p.symbol == order.symbol), None)

        if not existing_pos or existing_pos.quantity < order.quantity:
             return OrderResult(success=False, message="Insufficient position quantity")

        existing_pos.quantity -= order.quantity
        account.balance += cost
        account.buying_power += cost

        if existing_pos.quantity == 0:
            pos_list.remove(existing_pos)

    # Finalize order
    order.status = OrderStatus.FILLED
    order.filled_at = datetime.now(timezone.utc)
    _orders[order.id] = order

    return OrderResult(success=True, message="Order executed", order=order)

async def check_margin_requirement(account_id: str, order: Order) -> bool:
    # Simplified margin check
    if account_id not in _accounts:
        return False
    return True

async def calculate_portfolio_value(account_id: str) -> float:
    if account_id not in _accounts:
        return 0.0

    account = _accounts[account_id]
    pos_value = 0.0
    if account_id in _positions:
        for pos in _positions[account_id]:
            # Mock current price update slightly
            pos.current_price = pos.avg_cost # In real app, fetch market data
            pos_value += pos.quantity * pos.current_price

    account.portfolio_value = account.balance + pos_value
    return account.portfolio_value

def get_order_history() -> List[Order]:
    return list(_orders.values())

def get_positions(account_id: str) -> List[Position]:
    return _positions.get(account_id, [])

def get_account(account_id: str) -> Optional[TradingAccount]:
    return _accounts.get(account_id)

def get_order(order_id: str) -> Optional[Order]:
    return _orders.get(order_id)

def cancel_order(order_id: str) -> bool:
    if order_id in _orders:
        order = _orders[order_id]
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            return True
    return False
