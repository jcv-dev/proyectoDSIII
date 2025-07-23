import os
import pika
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

# --- Environment Variables ---
PERSISTENCE_SERVICE_URL = os.environ.get("PERSISTENCE_SERVICE_URL", "http://localhost:8001")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")

# --- FastAPI App ---
app = FastAPI()

@app.get("/{short_code}")
async def redirect_url(short_code: str):
    # --- Fetch from Persistence Service ---
    long_url = ""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PERSISTENCE_SERVICE_URL}/links/{short_code}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Short link not found.")
            response.raise_for_status()
            long_url = response.json()["long_url"]
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Persistence service is unavailable.")

    # --- Publish LinkAccessed Event ---
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue='link_accessed')
        channel.basic_publish(exchange='', routing_key='link_accessed', body=short_code)
        connection.close()
    except pika.exceptions.AMQPConnectionError:
        print("Warning: Could not connect to RabbitMQ to publish LinkAccessed event.")
        pass

    # --- Perform Redirect ---
    return RedirectResponse(url=long_url, status_code=307)