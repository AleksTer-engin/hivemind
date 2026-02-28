import asyncio
import json
import logging
import os
import requests
import asyncpg
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:8b")
DB_URL = os.getenv("DATABASE_URL", "postgresql://hivemind:hivemind@postgres:5432/hivemind")

# Топики
TOPIC_INGEST = "document.ingest"
TOPIC_CLASSIFIED = "document.classified"

async def classify_text(text: str) -> dict:
    """Отправляет текст в Qwen3 и получает классификацию"""
    prompt = f"""Классифицируй следующий текст по категориям: задача, идея, вопрос, заметка.
    Ответь только одним словом.
    
    Текст: {text}"""
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=30)
        
        if response.status_code == 200:
            result = response.json()["response"].strip()
            logger.info(f"Ollama ответ: {result}")
            
            # Определяем категорию и уверенность
            category = result.lower()
            if category not in ["задача", "идея", "вопрос", "заметка"]:
                category = "заметка"  # по умолчанию
            
            return {
                "tags": [category],
                "confidence": 0.9,
                "processing_time_ms": response.elapsed.total_seconds() * 1000
            }
        else:
            logger.error(f"Ошибка Ollama: {response.status_code}")
            return {"tags": ["ошибка"], "confidence": 0, "processing_time_ms": 0}
    except Exception as e:
        logger.error(f"Исключение при вызове Ollama: {e}")
        return {"tags": ["ошибка"], "confidence": 0, "processing_time_ms": 0}

async def save_to_db(document_id: str, classification: dict):
    """Сохранить классификацию в Postgres"""
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("""
            INSERT INTO classifications (document_id, tags, confidence, created_at)
            VALUES ($1, $2, $3, NOW())
        """, document_id, classification["tags"], classification["confidence"])
        await conn.close()
        logger.info(f"✅ Сохранено в БД: {document_id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения в БД: {e}")

async def message_handler(msg):
    """Обработчик сообщений из NATS (document.ingest)"""
    try:
        data = json.loads(msg.data.decode())
        logger.info(f"📥 Получен документ: {data.get('id', 'unknown')}")
        
        # Извлекаем данные согласно контракту ingest.yaml
        document_id = data.get("id")
        content = data.get("content", "")
        metadata = data.get("metadata", {})
        
        if not content:
            logger.warning("Пустой контент в документе")
            return
        
        # Классифицируем
        classification = await classify_text(content)
        
        # Сохраняем в БД
        if document_id:
            await save_to_db(document_id, classification)
        
        # Публикуем результат
        result = {
            "document_id": document_id,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "tags": classification["tags"],
            "confidence": classification["confidence"],
            "processing_time_ms": classification["processing_time_ms"],
            "metadata": metadata
        }
        
        await msg._client.publish(TOPIC_CLASSIFIED, json.dumps(result).encode())
        logger.info(f"📤 Опубликовано в {TOPIC_CLASSIFIED}: {result}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")

async def main():
    # Подключаемся к NATS
    nc = NATS()
    try:
        logger.info(f"🔄 Connecting to NATS at {NATS_URL}...")
        await nc.connect(NATS_URL)
        logger.info("✅ Connected to NATS")
        
        # Подписываемся на топик входящих документов
        await nc.subscribe(TOPIC_INGEST, cb=message_handler)
        logger.info(f"✅ Subscribed to {TOPIC_INGEST}")
        
        logger.info(f"🚀 Classifier service started. Model: {MODEL_NAME}")
        logger.info(f"📡 Waiting for messages on {TOPIC_INGEST}...")
        
        # Ждём сообщения вечно
        await asyncio.Future()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        await nc.drain()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())