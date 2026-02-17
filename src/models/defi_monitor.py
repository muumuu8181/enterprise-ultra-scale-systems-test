from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class ProtocolType(str, enum.Enum):
    DEX = "dex"
    LENDING = "lending"
    YIELD = "yield"
    BRIDGE = "bridge"

class OracleSource(str, enum.Enum):
    CHAINLINK = "chainlink"
    UNISWAP_TWAP = "uniswap_twap"
    API3 = "api3"

class DeFiProtocol(Base):
    __tablename__ = "defi_protocols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    chain: Mapped[str] = mapped_column(String)
    tvl_usd: Mapped[float] = mapped_column(Float)
    protocol_type: Mapped[ProtocolType] = mapped_column(Enum(ProtocolType))
    risk_score: Mapped[float] = mapped_column(Float)

class PriceOracle(Base):
    __tablename__ = "price_oracles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token_pair: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[OracleSource] = mapped_column(Enum(OracleSource))
    price_usd: Mapped[float] = mapped_column(Float)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deviation_pct: Mapped[float] = mapped_column(Float)

class FlashLoanAttack(Base):
    __tablename__ = "flash_loan_attacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    protocol_id: Mapped[int] = mapped_column(Integer, ForeignKey("defi_protocols.id"))
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attacker_address: Mapped[str] = mapped_column(String)
    profit_usd: Mapped[float] = mapped_column(Float)
    attack_type: Mapped[str] = mapped_column(String)
    tx_hash: Mapped[str] = mapped_column(String, unique=True)

    protocol: Mapped["DeFiProtocol"] = relationship("DeFiProtocol")
