import pytest
from fastapi.testclient import TestClient
from app.main import app
import hmac
import hashlib
import os

client = TestClient(app)
SECRET = "testsecret"
os.environ["WEBHOOK_SECRET"] = SECRET

def sign(body: bytes):
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

def test_webhook_valid():
    payload = {
        "message_id": "m1",
        "from": "+919876543210",
        "to": "+14155550100",
        "ts": "2025-01-15T10:00:00Z",
        "text": "Hello"
    }
    import json
    body = json.dumps(payload).encode()
    signature = sign(body)
    
    response = client.post(
        "/webhook", 
        content=body, 
        headers={"X-Signature": signature, "Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_webhook_invalid_sig():
    response = client.post(
        "/webhook", 
        json={"message_id": "m2"}, 
        headers={"X-Signature": "badsig"}
    )
    assert response.status_code == 401