import os
import pika
import httpx
import nanoid
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl

# --- Environment Variables ---
PERSISTENCE_SERVICE_URL = os.environ.get("PERSISTENCE_SERVICE_URL", "http://localhost:8001")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")

# --- Simple Circuit Breaker State ---
circuit_breaker_state = {
    "failure_count": 0,
    "last_failure_time": 0,
    "is_open": False,
    "fail_max": 3,
    "reset_timeout": 60
}

def check_circuit_breaker():
    """Check if circuit breaker allows the call"""
    current_time = time.time()
    
    # If circuit is open, check if we should reset it
    if circuit_breaker_state["is_open"]:
        if current_time - circuit_breaker_state["last_failure_time"] > circuit_breaker_state["reset_timeout"]:
            circuit_breaker_state["is_open"] = False
            circuit_breaker_state["failure_count"] = 0
            print("Circuit breaker reset - attempting call")
            return True
        else:
            print("Circuit breaker is open - blocking call")
            return False
    
    return True

def record_success():
    """Record successful call"""
    circuit_breaker_state["failure_count"] = 0
    circuit_breaker_state["is_open"] = False

def record_failure():
    """Record failed call and potentially open circuit"""
    circuit_breaker_state["failure_count"] += 1
    circuit_breaker_state["last_failure_time"] = time.time()
    
    if circuit_breaker_state["failure_count"] >= circuit_breaker_state["fail_max"]:
        circuit_breaker_state["is_open"] = True
        print(f"Circuit breaker opened after {circuit_breaker_state['failure_count']} failures")

# --- Pydantic Models ---
class URLShortenRequest(BaseModel):
    long_url: HttpUrl

# --- FastAPI App ---
app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"=== Incoming Request ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Path: {request.url.path}")
    print(f"Query: {request.url.query}")
    print(f"Headers: {dict(request.headers)}")
    print("========================")
    print(PERSISTENCE_SERVICE_URL)
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

@app.post("/", status_code=201)
async def shorten_url(request: URLShortenRequest):
    long_url = str(request.long_url)
    short_code = nanoid.generate(size=7)
    print("PASSED NANOID")
    
    # --- Circuit Breaker & Persistence Call ---
    if not check_circuit_breaker():
        raise HTTPException(status_code=503, detail="Service Unavailable: Circuit breaker is open")
    
    try:
        print("Making persistence call...")
        async with httpx.AsyncClient() as client:
            payload = {"short_code": short_code, "long_url": long_url}
            
            response = await client.post(
                f"{PERSISTENCE_SERVICE_URL}/links", 
                json=payload, 
                timeout=5.0
            )
            response.raise_for_status()  # Raise exception for HTTP errors
            record_success()
            print(f"Persistence call successful: {response.status_code}")
            
    except Exception as e:
        print(f"Error in persistence call: {e}")
        record_failure()
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {e}")
    
    # --- Saga: Publish LinkCreated Event ---
    try:
        print("Publishing to RabbitMQ...")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue='link_created')
        channel.basic_publish(exchange='', routing_key='link_created', body=short_code)
        connection.close()
        print("RabbitMQ publish successful")
    except pika.exceptions.AMQPConnectionError:
        # Handle case where message broker is down (log it, but don't fail the request)
        print("Warning: Could not connect to RabbitMQ to publish LinkCreated event.")
        pass
    except Exception as e:
        print(f"Unexpected RabbitMQ error: {e}")
        pass
    
    print("Returning response...")
    return {"short_url": f"/go/{short_code}"}