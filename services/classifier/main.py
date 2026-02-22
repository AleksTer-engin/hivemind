import asyncio
import json
import logging
import requests
from nats.aio.client import Client as NATS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"

async def classify_text(text: str) -> str:
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
            return result
        else:
            logger.error(f"Ошибка Ollama: {response.status_code}")
            return "ошибка"
    except Exception as e:
        logger.error(f"Исключение при вызове Ollama: {e}")
        return "ошибка"

async def message_handler(msg):
    """Обработчик сообщений из NATS"""
    try:
        data = json.loads(msg.data.decode())
        logger.info(f"Получен запрос: {data}")
        
        text = data.get("text", "")
        if not text:
            logger.warning("Пустой текст в запросе")
            await msg.respond(json.dumps({"error": "empty text"}).encode())
            return
        
        # Классифицируем
        category = await classify_text(text)
        
        # Отправляем ответ
        response = {"text": text, "category": category}
        await msg.respond(json.dumps(response).encode())
        logger.info(f"Отправлен ответ: {response}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        await msg.respond(json.dumps({"error": str(e)}).encode())

async def main():
    # Подключаемся к NATS
    nc = NATS()
    try:
        await nc.connect("nats://localhost:4222")
        logger.info("✅ Connected to NATS")
        
        # Подписываемся на топик
        sub = await nc.subscribe("classify.request", cb=message_handler)
        logger.info("✅ Subscribed to classify.request")
        
        logger.info("🚀 Classifier service started. Waiting for messages...")
        
        # Ждём сообщения вечно
        await asyncio.Future()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        await sub.unsubscribe()
        await nc.close()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())