import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_upload_no_user():
    response = client.post("/documents/upload")
    assert response.status_code == 422

def test_search_no_query():
    response = client.get("/search")
    assert response.status_code == 422
