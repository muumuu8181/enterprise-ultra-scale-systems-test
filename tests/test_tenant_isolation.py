import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.v1.billing import router as billing_router

def test_cross_tenant_data_access_blocked():
    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    # Tenant A tries to access Tenant B's subscription
    tenant_a_id = "tenant-a"
    tenant_b_id = "tenant-b"

    # We simulate a request where the "authenticated user" (via header X-Tenant-ID) is "tenant-a",
    # but the requested resource is for "tenant-b".

    response = client.get(
        f"/tenants/{tenant_b_id}/subscription",
        headers={"X-Tenant-ID": tenant_a_id}
    )

    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}"
    assert response.json()["detail"] == "Cross-tenant access forbidden"

def test_same_tenant_access_allowed():
    app = FastAPI()
    app.include_router(billing_router)
    client = TestClient(app)

    tenant_a_id = "tenant-a"

    response = client.get(
        f"/tenants/{tenant_a_id}/subscription",
        headers={"X-Tenant-ID": tenant_a_id}
    )

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    assert response.json()["tenant_id"] == tenant_a_id
