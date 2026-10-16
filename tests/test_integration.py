import os
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

def test_web_health():
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_database_health():
    response = requests.get(f"{BASE_URL}/api/db-health", timeout=5)
    assert response.status_code == 200
    assert response.json()["database"] == "reachable"

def test_customers_endpoint():
    response = requests.get(f"{BASE_URL}/api/customers", timeout=5)
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)
    assert len(customers) >= 3
