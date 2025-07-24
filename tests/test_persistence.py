import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sqlalchemy
from sqlalchemy.orm import Session

# Setup test environment
from your_module import app, Link, LinkCreate, LinkResponse  # replace 'your_module' with your actual module name

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db_session():
    with patch('your_module.SessionLocal') as mock:
        mock_session = MagicMock(spec=Session)
        mock.return_value = mock_session
        yield mock_session

def test_create_link_success(client, mock_db_session):
    # Setup
    test_data = {"short_code": "abc123", "long_url": "https://example.com"}
    mock_db_session.commit.return_value = None
    mock_db_session.refresh.return_value = None
    
    # Test
    response = client.post("/links", json=test_data)
    
    # Verify
    assert response.status_code == 201
    assert response.json()["short_code"] == test_data["short_code"]
    assert response.json()["long_url"] == test_data["long_url"]
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()

def test_create_link_conflict(client, mock_db_session):
    # Setup
    test_data = {"short_code": "abc123", "long_url": "https://example.com"}
    mock_db_session.commit.side_effect = sqlalchemy.exc.IntegrityError(None, None, None)
    
    # Test
    response = client.post("/links", json=test_data)
    
    # Verify
    assert response.status_code == 409
    assert "Short code already exists" in response.json()["detail"]
    mock_db_session.rollback.assert_called_once()

def test_get_link_success(client, mock_db_session):
    # Setup
    mock_link = Link(short_code="abc123", long_url="https://example.com")
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_link
    
    # Test
    response = client.get("/links/abc123")
    
    # Verify
    assert response.status_code == 200
    assert response.json()["short_code"] == "abc123"
    assert response.json()["long_url"] == "https://example.com"
    mock_db_session.query.assert_called_once_with(Link)

def test_get_link_not_found(client, mock_db_session):
    # Setup
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    # Test
    response = client.get("/links/nonexistent")
    
    # Verify
    assert response.status_code == 404
    assert "Link not found" in response.json()["detail"]