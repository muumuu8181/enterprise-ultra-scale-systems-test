import pytest
from src.models.scim_models import Organization, Group, SCIMOperation
from src.services.sso_service import Identity, TokenPair
from src.api.v1.scim import router as scim_router
from src.api.v1.sso import router as sso_router

def test_models_import():
    assert Organization.__tablename__ == 'organizations'
    assert Group.__tablename__ == 'groups'
    assert SCIMOperation.__tablename__ == 'scim_operations'

def test_schemas_instantiate():
    id = Identity(id="1", email="test@test.com")
    assert id.id == "1"
    token = TokenPair(access_token="a", refresh_token="r")
    assert token.access_token == "a"

def test_routers_exist():
    assert scim_router is not None
    assert sso_router is not None
