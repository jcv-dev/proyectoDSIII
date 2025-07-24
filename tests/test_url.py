import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import time
import pika

# Setup test environment
from your_module import app, circuit_breaker_state  # replace 'your_module' with your actual module name

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def reset_circuit_breaker():
    """Reset circuit breaker state before each test"""
    circuit_breaker_state.update({
        "failure_count": 0,
        "last_failure_time": 0,
        "is_open": False,
        "fail_max": 3,
        "reset_timeout": 60
    })

@pytest.fixture
def mock_httpx():
    with patch('your_module.httpx.AsyncClient') as mock:
        yield mock

@pytest.fixture
def mock_pika():
    with patch('your_module.pika.BlockingConnection') as mock:
        mock_connection = MagicMock()
        mock.return_value = mock_connection
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        yield mock_channel

def test_shorten_url_success(client, mock_httpx, mock_pika, reset_circuit_breaker):
    # Mock HTTPX response
    mock_client = AsyncMock()
    mock_httpx.return_value.__aenter__.return_value = mock_client
    mock_client.post.return_value = httpx.Response(201, json={"short_code": "abc123", "long_url": "https://example.com"})
    
    # Test
    response = client.post("/", json={"long_url": "https://example.com"})
    
    # Verify
    assert response.status_code == 201
    assert "short_url" in response.json()
    assert "/go/" in response.json()["short_url"]
    mock_client.post.assert_called_once()

def test_shorten_url_circuit_breaker_open(client, reset_circuit_breaker):
    # Force circuit breaker open
    circuit_breaker_state.update({
        "is_open": True,
        "last_failure_time": time.time()
    })
    
    # Test
    response = client.post("/", json={"long_url": "https://example.com"})
    
    # Verify
    assert response.status_code == 503
    assert "Circuit breaker is open" in response.json()["detail"]

def test_shorten_url_persistence_failure(client, mock_httpx, reset_circuit_breaker):
    # Mock HTTPX to raise exception
    mock_client = AsyncMock()
    mock_httpx.return_value.__aenter__.return_value = mock_client
    mock_client.post.side_effect = httpx.ConnectError("Connection failed")
    
    # Test
    response = client.post("/", json={"long_url": "https://example.com"})
    
    # Verify
    assert response.status_code == 503
    assert "Service Unavailable" in response.json()["detail"]
    assert circuit_breaker_state["failure_count"] == 1

def test_shorten_url_rabbitmq_failure(client, mock_httpx, mock_pika, reset_circuit_breaker):
    # Mock successful HTTPX response but failed RabbitMQ
    mock_client = AsyncMock()
    mock_httpx.return_value.__aenter__.return_value = mock_client
    mock_client.post.return_value = httpx.Response(201)
    
    # Make RabbitMQ raise connection error
    mock_pika.side_effect = pika.exceptions.AMQPConnectionError
    
    # Test (should still succeed since RabbitMQ failure is handled gracefully)
    response = client.post("/", json={"long_url": "https://example.com"})
    
    # Verify
    assert response.status_code == 201
    assert "short_url" in response.json()

def test_request_logging_middleware(client, mock_httpx, mock_pika, reset_circuit_breaker, capsys):
    # Mock successful response
    mock_client = AsyncMock()
    mock_httpx.return_value.__aenter__.return_value = mock_client
    mock_client.post.return_value = httpx.Response(201)
    
    # Test
    response = client.post("/", json={"long_url": "https://example.com"})
    
    # Verify logging occurred
    captured = capsys.readouterr()
    assert "Incoming Request" in captured.out
    assert "Method: POST" in captured.out
    assert "Response status: 201" in captured.out