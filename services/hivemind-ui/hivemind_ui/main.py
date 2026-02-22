# hivemind_ui/main.py
import dash
from dash import dcc, html, Input, Output, State
import nats
import json
import asyncio
import threading
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = dash.Dash(__name__)

# Храним историю сообщений
messages = deque(maxlen=50)
# Для потокобезопасности
lock = threading.Lock()

class NatsListener:
    def __init__(self):
        self.nc = None
        self.loop = None
        self.thread = None
        
    def start(self):
        """Запускаем listener в отдельном потоке"""
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def _run_loop(self):
        """Создаем event loop для потока"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._listen())
    
    async def _listen(self):
        """Подключаемся к NATS и слушаем ответы"""
        try:
            self.nc = await nats.connect("nats://nats:4222")
            logger.info("✅ UI connected to NATS")
            
            # Подписываемся на топик с ответами классификатора
            await self.nc.subscribe("classify.response", cb=self._on_response)
            logger.info("✅ Subscribed to classify.response")
            
            # Держим соединение открытым
            await asyncio.Future()
        except Exception as e:
            logger.error(f"❌ NATS error: {e}")
    
    async def _on_response(self, msg):
        """Обработчик входящих ответов"""
        try:
            data = json.loads(msg.data.decode())
            with lock:
                messages.appendleft(f"🤖 Qwen3: {data.get('category', '?')} - {data.get('text', '')}")
            logger.info(f"Received response: {data}")
        except Exception as e:
            logger.error(f"Error processing response: {e}")

# Запускаем listener
listener = NatsListener()
listener.start()

async def send_to_nats(text):
    """Отправляем запрос в NATS и ждём ответ"""
    try:
        nc = await nats.connect("nats://nats:4222")
        # Используем request вместо publish
        response = await nc.request("classify.request", json.dumps({"text": text}).encode(), timeout=5)
        data = json.loads(response.data.decode())
        with lock:
            messages.appendleft(f"Вы: {text}")
            messages.appendleft(f"🤖 Qwen3: {data.get('category', '?')} - {text}")
        logger.info(f"Received response: {data}")
        await nc.close()
    except Exception as e:
        logger.error(f"Error sending to NATS: {e}")
        with lock:
            messages.appendleft(f"Вы: {text}")
            messages.appendleft(f"❌ Ошибка: {e}")

def send_message(text):
    """Запускаем отправку в отдельном потоке"""
    asyncio.run(send_to_nats(text))

app.layout = html.Div([
    html.H1("🐝 HiveMind Chat", style={"textAlign": "center"}),
    
    # История сообщений
    html.Div(id="chat-history", style={
        "height": "500px",
        "overflow-y": "scroll",
        "border": "1px solid #ddd",
        "margin": "20px",
        "padding": "10px",
        "backgroundColor": "#f9f9f9"
    }),
    
    # Поле ввода (внизу по центру)
    html.Div([
        dcc.Textarea(
            id="chat-input",
            placeholder="Напишите сообщение...",
            style={
                "width": "60%",
                "height": "80px",
                "margin": "10px auto",
                "display": "block",
                "padding": "10px",
                "fontSize": "16px"
            }
        ),
        html.Button(
            "Отправить",
            id="send-btn",
            style={
                "display": "block",
                "margin": "10px auto",
                "padding": "10px 30px",
                "fontSize": "16px",
                "backgroundColor": "#4CAF50",
                "color": "white",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer"
            }
        )
    ]),
    
    dcc.Interval(id="update", interval=500)  # Обновление каждые 0.5 сек
])

@app.callback(
    Output("chat-history", "children"),
    Input("update", "n_intervals")
)
def update_chat(_):
    """Обновляем историю сообщений"""
    with lock:
        current_messages = list(messages)
    
    return [
        html.Div(msg, style={
            "padding": "8px",
            "margin": "5px",
            "borderRadius": "5px",
            "backgroundColor": "#e3f2fd" if msg.startswith("Вы:") else "#fff3e0"
        }) for msg in current_messages
    ]

@app.callback(
    Output("chat-input", "value"),
    Input("send-btn", "n_clicks"),
    State("chat-input", "value"),
    prevent_initial_call=True
)
def on_send(n_clicks, value):
    """Обработчик отправки сообщения"""
    if value and value.strip():
        # Отправляем в NATS в фоне
        threading.Thread(target=send_message, args=(value.strip(),)).start()
    return ""  # Очищаем поле ввода

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)