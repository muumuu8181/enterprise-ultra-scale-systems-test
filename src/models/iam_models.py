from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime, timezone

Base = declarative_base()

class IdentityStatus(str, enum.Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    PENDING = "pending"

class RoleScope(str, enum.Enum):
    GLOBAL = "global"
    ORG = "org"
    RESOURCE = "resource"

class PrincipalType(str, enum.Enum):
    USER = "user"
    GROUP = "group"
    SERVICE = "service"

class PolicyEffect(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"

class Identity(Base):
    __tablename__ = "identities"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    risk_score = Column(Float, default=0.0)
    status = Column(Enum(IdentityStatus), default=IdentityStatus.PENDING)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(JSON, nullable=False)
    scope = Column(Enum(RoleScope), default=RoleScope.GLOBAL)
    parent_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)

    parent_role = relationship("Role", remote_side=[id], backref="child_roles")

class ResourcePolicy(Base):
    __tablename__ = "resource_policies"

    id = Column(Integer, primary_key=True, index=True)
    resource_type = Column(String, index=True, nullable=False)
    resource_id = Column(String, index=True, nullable=False)
    principal_type = Column(Enum(PrincipalType), nullable=False)
    effect = Column(Enum(PolicyEffect), nullable=False)
    conditions = Column(JSON, nullable=True)
