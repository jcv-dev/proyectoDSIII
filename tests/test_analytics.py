import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import os

# Setup test environment variables
os.environ["MONGO_URL"] = "mongodb://mock:mock@localhost:27017/"
os.environ["RABBITMQ_HOST"] = "localhost"

from your_module import app  # replace 'your_module' with your actual module name

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_mongo():
    with patch("your_module.analytics_collection") as mock:
        yield mock

@pytest.mark.asyncio
async def test_get_analytics_success(client, mock_mongo):
    # Setup mock response
    mock_data = {"short_code": "abc123", "clicks": 42}
    mock_mongo.find_one = AsyncMock(return_value=mock_data)
    
    # Make request
    response = client.get("/api/analytics/abc123")
    
    # Verify response
    assert response.status_code == 200
    assert response.json() == mock_data
    mock_mongo.find_one.assert_called_once_with({"short_code": "abc123"}, {"_id": 0})

@pytest.mark.asyncio
async def test_get_analytics_not_found(client, mock_mongo):
    # Setup mock to return None (not found)
    mock_mongo.find_one = AsyncMock(return_value=None)
    
    # Make request
    response = client.get("/api/analytics/nonexistent")
    
    # Verify response
    assert response.status_code == 200
    assert response.json() == {"message": "No analytics found for this link."}
    mock_mongo.find_one.assert_called_once_with({"short_code": "nonexistent"}, {"_id": 0})

@pytest.mark.asyncio
async def test_get_analytics_error(client, mock_mongo):
    # Setup mock to raise an exception
    mock_mongo.find_one = AsyncMock(side_effect=Exception("DB error"))
    
    # Make request
    response = client.get("/api/analytics/error")
    
    # Verify error response
    assert response.status_code == 500
    assert "error" in response.json()