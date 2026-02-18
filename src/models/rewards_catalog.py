from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Reward(Base):
    __tablename__ = 'rewards'

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # travel, merchandise, experience, cashback
    points_cost = Column(Integer, nullable=False)
    inventory = Column(Integer, nullable=False)
    expiry = Column(DateTime, nullable=True)

class PartnerRedemption(Base):
    __tablename__ = 'partner_redemptions'

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False)
    reward_type = Column(String, nullable=False)
    conversion_rate = Column(Float, nullable=False)
    min_points = Column(Integer, nullable=False)

class PromotionCampaign(Base):
    __tablename__ = 'promotion_campaigns'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    multiplier = Column(Float, nullable=False)
    conditions = Column(JSON, nullable=True)
    segments = Column(JSON, nullable=True)
