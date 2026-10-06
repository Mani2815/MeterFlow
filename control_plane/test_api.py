from fastapi.testclient import TestClient
from control_plane.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_ingestion_run():
    response = client.post("/ingestion/run", json={"table": "customers", "batch_size": 100})
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "STARTED"

def test_backfill():
    response = client.post("/backfill", json={"table": "bills", "start_date": "2020-01-01", "end_date": "2020-12-31"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "STARTED"
    
def test_missing_run():
    response = client.get("/runs/does_not_exist")
    assert response.status_code == 404

def test_correlation_id():
    response = client.get("/health", headers={"X-Correlation-ID": "test-uuid"})
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "test-uuid"
