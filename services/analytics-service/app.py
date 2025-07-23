import os
import pika
import threading
import asyncio
import motor.motor_asyncio
from fastapi import FastAPI

# --- Environment Variables ---
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://root:example@localhost:27017/")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")

# --- MongoDB Setup ---
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.analytics_db
analytics_collection = db.get_collection("clicks")

# --- FastAPI App ---
app = FastAPI()

# --- Global variable to hold the main event loop ---
main_loop = None

# --- Helper function to extract short code from URL ---
def extract_short_code(url: str) -> str:
    """Extract short code from URL by taking everything after the last '/'"""
    return url.rstrip('/').split('/')[-1]

# --- RabbitMQ Consumer Logic ---
def rabbitmq_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, heartbeat=600, blocked_connection_timeout=300))
    channel = connection.channel()
    
    # Declare queues
    channel.queue_declare(queue='link_created')
    channel.queue_declare(queue='link_accessed')
    
    def on_link_created(ch, method, properties, body):
        url = body.decode()
        short_code = extract_short_code(url)
        print(f" [x] Received LinkCreated for URL: {url}, extracted short_code: {short_code}")
        
        async def insert_analytics():
            await analytics_collection.insert_one({"short_code": short_code, "clicks": 0})
        
        # Schedule the coroutine to run on the main event loop
        future = asyncio.run_coroutine_threadsafe(insert_analytics(), main_loop)
        try:
            future.result() # Wait for the coroutine to complete
        except Exception as e:
            print(f"Error inserting analytics: {e}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def on_link_accessed(ch, method, properties, body):
        url = body.decode()
        short_code = extract_short_code(url)
        print(f" [x] Received LinkAccessed for URL: {url}, extracted short_code: {short_code}")
        
        async def update_analytics():
            await analytics_collection.update_one({"short_code": short_code}, {"$inc": {"clicks": 1}})
        
        # Schedule the coroutine to run on the main event loop
        future = asyncio.run_coroutine_threadsafe(update_analytics(), main_loop)
        try:
            future.result() # Wait for the coroutine to complete
        except Exception as e:
            print(f"Error updating analytics: {e}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    channel.basic_consume(queue='link_created', on_message_callback=on_link_created)
    channel.basic_consume(queue='link_accessed', on_message_callback=on_link_accessed)
    
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop() # Store the main event loop
    
    # Start RabbitMQ consumer in a background thread
    consumer_thread = threading.Thread(target=rabbitmq_consumer, daemon=True)
    consumer_thread.start()

@app.get("/api/analytics/{short_code}")
async def get_analytics(short_code: str):
    data = await analytics_collection.find_one({"short_code": short_code}, {"_id": 0})
    if data:
        return data
    return {"message": "No analytics found for this link."}