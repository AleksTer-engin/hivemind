import asyncio
import logging
from nats.aio.client import Client as NATS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NATS_URL = "nats://nats:4222"
TOPIC_SUBSCRIBE = "document.classified"
TOPIC_PUBLISH = "document.embedded"

async def message_handler(msg):
    try:
        data = msg.data.decode()
        logger.info(f"📥 Received: {data}")
        
        # TODO: здесь будет создание эмбеддингов
        
        response = {"status": "embedded", "original": data}
        await msg._client.publish(TOPIC_PUBLISH, str(response).encode())
        logger.info(f"📤 Published to {TOPIC_PUBLISH}")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def main():
    nc = NATS()
    try:
        logger.info(f"🔄 Connecting to NATS at {NATS_URL}...")
        await nc.connect(NATS_URL)
        logger.info("✅ Connected to NATS")
        
        await nc.subscribe(TOPIC_SUBSCRIBE, cb=message_handler)
        logger.info(f"✅ Subscribed to {TOPIC_SUBSCRIBE}")
        
        logger.info(f"🚀 Embedder service started (mock)")
        logger.info(f"📡 Waiting for messages on {TOPIC_SUBSCRIBE}...")
        
        await asyncio.Future()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        await nc.drain()

if __name__ == "__main__":
    asyncio.run(main())
