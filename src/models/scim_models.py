from sqlalchemy import Column, Integer, String, JSON, Enum, ForeignKey
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    domain = Column(String, unique=True, index=True)
    sso_config = Column(JSON)
    scim_endpoint = Column(String)
    provisioning_status = Column(String)

class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey('organizations.id'))
    name = Column(String)
    members = Column(JSON)
    auto_assign_roles = Column(JSON)

class SCIMOpType(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    sync = "sync"

class EntityType(str, enum.Enum):
    user = "user"
    group = "group"

class SCIMOperation(Base):
    __tablename__ = 'scim_operations'

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey('organizations.id'))
    op_type = Column(Enum(SCIMOpType))
    entity_type = Column(Enum(EntityType))
    status = Column(String)
