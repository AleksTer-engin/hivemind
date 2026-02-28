# hivemind_ui/main.py
import dash
from dash import dcc, html, Input, Output, State
import nats
import json
import asyncio
import threading
from collections import deque
import logging
import plotly.graph_objects as go
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = dash.Dash(__name__, suppress_callback_exceptions=True)

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

# Тестовые данные для целей
goals_data = [
    {
        "id": "1",
        "title": "Завершить HiveMind MVP",
        "priority": "P1",
        "status": "active",
        "progress": 75,
        "due_date": "2026-03-15",
        "actor": "Служащий",
        "sphere": "Служение"
    },
    {
        "id": "2",
        "title": "Написать статью про классификатор",
        "priority": "P2",
        "status": "active",
        "progress": 30,
        "due_date": "2026-03-07",
        "actor": "Творец",
        "sphere": "Творчество"
    },
    {
        "id": "3",
        "title": "Интегрировать Goals Service",
        "priority": "P1",
        "status": "done",
        "progress": 100,
        "due_date": "2026-02-28",
        "actor": "Служащий",
        "sphere": "Служение"
    }
]

# Вспомогательная функция для создания чекбокса
def create_checkbox(id):
    return html.Span("☐", style={"marginRight": "10px", "fontSize": "20px", "cursor": "pointer"})

# Layout для страницы целей
goals_layout = html.Div([
    html.H1("🎯 Цели и задачи", style={"textAlign": "center", "marginBottom": "30px"}),
    
    # Вкладки
    dcc.Tabs([
        dcc.Tab(label="📋 Список целей", children=[
            html.Div([
                # Фильтры
                html.Div([
                    dcc.Dropdown(
                        options=[
                            {"label": "Все", "value": "all"},
                            {"label": "Активные", "value": "active"},
                            {"label": "Завершённые", "value": "done"},
                        ],
                        value="all",
                        style={"width": "200px", "display": "inline-block", "marginRight": "10px"}
                    ),
                    dcc.Dropdown(
                        options=[
                            {"label": "Все приоритеты", "value": "all"},
                            {"label": "P1", "value": "P1"},
                            {"label": "P2", "value": "P2"},
                            {"label": "P3", "value": "P3"},
                        ],
                        value="all",
                        style={"width": "200px", "display": "inline-block", "marginRight": "10px"}
                    ),
                    dcc.Dropdown(
                        options=[
                            {"label": "Все акторы", "value": "all"},
                            {"label": "Служащий", "value": "Служащий"},
                            {"label": "Творец", "value": "Творец"},
                            {"label": "Исследователь", "value": "Исследователь"},
                        ],
                        value="all",
                        style={"width": "200px", "display": "inline-block"}
                    )
                ], style={"marginBottom": "20px"}),
                
                # Список целей
                html.Div([
                    html.Div([
                        html.Div([
                            create_checkbox(g['id']),
                            html.Span(g['title'], style={"fontWeight": "bold", "fontSize": "16px"}),
                            html.Span(f" [{g['actor']} | {g['sphere']}]", style={"color": "#666", "marginLeft": "10px"})
                        ], style={"display": "flex", "alignItems": "center"}),
                        
                        html.Div([
                            html.Div([
                                html.Span(f"Приоритет: {g['priority']}", 
                                         style={"color": "#f00" if g['priority']=="P1" else "#ff0" if g['priority']=="P2" else "#0f0"}),
                                html.Span(f" | Срок: {g['due_date']}", style={"marginLeft": "20px"})
                            ], style={"marginBottom": "5px"}),
                            
                            html.Div([
                                html.Div(style={
                                    "width": f"{g['progress']}%",
                                    "height": "10px",
                                    "backgroundColor": "#4CAF50",
                                    "borderRadius": "5px"
                                })
                            ], style={
                                "width": "100%",
                                "backgroundColor": "#ddd",
                                "borderRadius": "5px",
                                "marginTop": "5px"
                            }),
                            html.Span(f"{g['progress']}%", style={"fontSize": "12px", "color": "#666"})
                        ], style={"marginLeft": "30px", "marginTop": "5px"})
                    ], style={
                        "padding": "15px",
                        "border": "1px solid #ddd",
                        "borderRadius": "5px",
                        "marginBottom": "10px",
                        "backgroundColor": "#f9f9f9"
                    }) for g in goals_data
                ])
            ], style={"padding": "20px"})
        ]),
        
        dcc.Tab(label="🌳 Дерево целей", children=[
            html.Div([
                dcc.Graph(
                    figure={
                        'data': [go.Treemap(
                            labels=['HiveMind', 'Фаза 1', 'API Gateway', 'Classifier', 'Базы данных',
                                    'Фаза 2', 'Embedder', 'Linker', 'Goals Service'],
                            parents=['', 'HiveMind', 'Фаза 1', 'Фаза 1', 'Фаза 1',
                                    'HiveMind', 'Фаза 2', 'Фаза 2', 'Фаза 2'],
                            values=[0, 0, 100, 100, 100, 0, 80, 70, 40],
                            textinfo="label+value+percent parent",
                            marker=dict(colors=['lightblue', 'lightgreen', 'gold', 'gold', 'gold',
                                               'lightgreen', 'orange', 'orange', 'orange'])
                        )],
                        'layout': go.Layout(
                            margin=dict(t=50, l=25, r=25, b=25)
                        )
                    }
                ),
                html.Div([
                    html.Span("🟢 Завершено", style={"marginRight": "20px"}),
                    html.Span("🟡 В процессе", style={"marginRight": "20px"}),
                    html.Span("🔴 Начато", style={"marginRight": "20px"})
                ], style={"marginTop": "20px", "textAlign": "center"})
            ], style={"padding": "20px"})
        ]),
        
        dcc.Tab(label="📊 Доска задач", children=[
            html.Div([
                html.Div([
                    # Колонка TODO
                    html.Div([
                        html.H3("📋 Нужно сделать", style={"textAlign": "center"}),
                        html.Div([
                            html.Div([
                                html.H4("Написать Goals Service", style={"margin": "0"}),
                                html.P("👤 AI | 🔴 P1"),
                                html.Button("➡️", style={"width": "100%"})
                            ], style={
                                "padding": "10px",
                                "backgroundColor": "#fff",
                                "borderRadius": "5px",
                                "marginBottom": "10px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }),
                            html.Div([
                                html.H4("Интегрировать с UI", style={"margin": "0"}),
                                html.P("👤 welem | 🔴 P1"),
                                html.Button("➡️", style={"width": "100%"})
                            ], style={
                                "padding": "10px",
                                "backgroundColor": "#fff",
                                "borderRadius": "5px",
                                "marginBottom": "10px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            })
                        ], style={
                            "minHeight": "400px",
                            "backgroundColor": "#f4f4f4",
                            "borderRadius": "5px",
                            "padding": "10px"
                        })
                    ], style={"width": "23%", "display": "inline-block", "margin": "1%"}),
                    
                    # Колонка IN PROGRESS
                    html.Div([
                        html.H3("⚡ В процессе", style={"textAlign": "center"}),
                        html.Div([
                            html.Div([
                                html.H4("UI для целей", style={"margin": "0"}),
                                html.P("👤 welem | 🔴 P1"),
                                html.Div(style={"width": "100%", "backgroundColor": "#4CAF50", "height": "5px", "borderRadius": "5px", "width": "50%"}),
                                html.Div([
                                    html.Button("◀️", style={"width": "48%"}),
                                    html.Button("➡️", style={"width": "48%", "marginLeft": "4%"})
                                ], style={"marginTop": "10px"})
                            ], style={
                                "padding": "10px",
                                "backgroundColor": "#fff",
                                "borderRadius": "5px",
                                "marginBottom": "10px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            })
                        ], style={
                            "minHeight": "400px",
                            "backgroundColor": "#f4f4f4",
                            "borderRadius": "5px",
                            "padding": "10px"
                        })
                    ], style={"width": "23%", "display": "inline-block", "margin": "1%"}),
                    
                    # Колонка REVIEW
                    html.Div([
                        html.H3("👀 На проверке", style={"textAlign": "center"}),
                        html.Div([
                            html.Div([
                                html.H4("API Gateway", style={"margin": "0"}),
                                html.P("👤 AI | 🔴 P1"),
                                html.Button("✅ Принять", style={"width": "100%"})
                            ], style={
                                "padding": "10px",
                                "backgroundColor": "#fff",
                                "borderRadius": "5px",
                                "marginBottom": "10px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            })
                        ], style={
                            "minHeight": "400px",
                            "backgroundColor": "#f4f4f4",
                            "borderRadius": "5px",
                            "padding": "10px"
                        })
                    ], style={"width": "23%", "display": "inline-block", "margin": "1%"}),
                    
                    # Колонка DONE
                    html.Div([
                        html.H3("✅ Готово", style={"textAlign": "center"}),
                        html.Div([
                            html.Div([
                                html.H4("✓ База данных", style={"margin": "0", "color": "#666"}),
                                html.P("👤 AI")
                            ], style={
                                "padding": "10px",
                                "backgroundColor": "#e8f5e8",
                                "borderRadius": "5px",
                                "marginBottom": "10px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            }),
                            html.Div([
                                html.H4("✓ NATS", style={"margin": "0", "color": "#666"}),
                                html.P("👤 AI")
                            ], style={
                                "padding": "10px",
                                "backgroundColor": "#e8f5e8",
                                "borderRadius": "5px",
                                "marginBottom": "10px",
                                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                            })
                        ], style={
                            "minHeight": "400px",
                            "backgroundColor": "#f4f4f4",
                            "borderRadius": "5px",
                            "padding": "10px"
                        })
                    ], style={"width": "23%", "display": "inline-block", "margin": "1%"})
                ], style={"display": "flex", "flexWrap": "wrap"})
            ], style={"padding": "20px"})
        ]),
        
        dcc.Tab(label="➕ Новая цель", children=[
            html.Div([
                html.H3("Создать новую цель", style={"marginBottom": "20px"}),
                
                html.Div([
                    html.Div([
                        html.Label("Название цели *"),
                        dcc.Input(type="text", id="goal-title", style={"width": "100%", "padding": "8px"}),
                        
                        html.Label("Описание", style={"marginTop": "15px"}),
                        dcc.Textarea(id="goal-desc", style={"width": "100%", "height": "100px", "padding": "8px"}),
                        
                        html.Label("Приоритет", style={"marginTop": "15px"}),
                        dcc.Slider(
                            id="goal-priority",
                            min=1, max=4, value=3,
                            marks={1: "P1 (крит)", 2: "P2 (выс)", 3: "P3 (сред)", 4: "P4 (низ)"}
                        ),
                        
                        html.Label("Срок", style={"marginTop": "15px"}),
                        dcc.DatePickerSingle(id="goal-due", date=datetime.now().date())
                    ], style={"width": "45%", "display": "inline-block", "verticalAlign": "top", "padding": "10px"}),
                    
                    html.Div([
                        html.Label("Актор"),
                        dcc.Dropdown(
                            id="goal-actor",
                            options=[
                                {"label": "Выживающий", "value": "Выживающий"},
                                {"label": "Накапливающий", "value": "Накапливающий"},
                                {"label": "Общающийся", "value": "Общающийся"},
                                {"label": "Хранитель", "value": "Хранитель"},
                                {"label": "Играющий", "value": "Играющий"},
                                {"label": "Служащий", "value": "Служащий"},
                                {"label": "Соревнующийся", "value": "Соревнующийся"},
                                {"label": "Трансформирующийся", "value": "Трансформирующийся"}
                            ],
                            value="Служащий"
                        ),
                        
                        html.Label("Сфера", style={"marginTop": "15px"}),
                        dcc.Dropdown(
                            id="goal-sphere",
                            options=[
                                {"label": "Биологическое Я", "value": "Биологическое Я"},
                                {"label": "Ресурсы", "value": "Ресурсы"},
                                {"label": "Коммуникация", "value": "Коммуникация"},
                                {"label": "Внутренний Очаг", "value": "Внутренний Очаг"},
                                {"label": "Творчество", "value": "Творчество"},
                                {"label": "Служение", "value": "Служение"},
                                {"label": "Партнёрство", "value": "Партнёрство"},
                                {"label": "Трансформация", "value": "Трансформация"}
                            ],
                            value="Служение"
                        ),
                        
                        html.Label("Родительская цель", style={"marginTop": "15px"}),
                        dcc.Dropdown(
                            id="goal-parent",
                            options=[
                                {"label": "Нет", "value": ""},
                                {"label": "Завершить HiveMind MVP", "value": "1"},
                                {"label": "Фаза 2: Интеллект", "value": "2"}
                            ],
                            value=""
                        ),
                        
                        html.Label("Теги", style={"marginTop": "15px"}),
                        dcc.Input(type="text", id="goal-tags", placeholder="через запятую", style={"width": "100%"})
                    ], style={"width": "45%", "display": "inline-block", "verticalAlign": "top", "padding": "10px", "marginLeft": "5%"})
                ]),
                
                html.Button("🚀 Создать цель", id="create-goal-btn", 
                           style={
                               "display": "block",
                               "margin": "20px auto",
                               "padding": "10px 40px",
                               "backgroundColor": "#4CAF50",
                               "color": "white",
                               "border": "none",
                               "borderRadius": "5px",
                               "fontSize": "16px",
                               "cursor": "pointer"
                           }),
                
                html.Div(id="create-goal-output")
            ], style={"padding": "20px"})
        ])
    ])
])

# Создаём layout с навигацией
app.layout = html.Div([
    # Заголовок
    html.H1("🐝 HiveMind", style={"textAlign": "center", "marginBottom": "20px"}),
    
    # Навигационное меню
    html.Div([
        dcc.Link("🏠 Чат", href="/", style={"margin": "10px", "fontSize": "18px", "textDecoration": "none"}),
        dcc.Link("🎯 Цели", href="/goals", style={"margin": "10px", "fontSize": "18px", "textDecoration": "none"}),
        dcc.Link("📊 Граф", href="/graph", style={"margin": "10px", "fontSize": "18px", "textDecoration": "none"}),
    ], style={"textAlign": "center", "marginBottom": "20px"}),
    
    # Контент страниц
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# Callback для роутинга
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/goals":
        return goals_layout
    else:
        # Главная страница (чат)
        return html.Div([
            # История сообщений
            html.Div(id="chat-history", style={
                "height": "500px",
                "overflow-y": "scroll",
                "border": "1px solid #ddd",
                "margin": "20px",
                "padding": "10px",
                "backgroundColor": "#f9f9f9"
            }),
            
            # Поле ввода
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
            
            dcc.Interval(id="update", interval=500)
        ])

# Callback для обновления чата
@app.callback(
    Output("chat-history", "children"),
    Input("update", "n_intervals")
)
def update_chat(_):
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

# Callback для отправки сообщения
@app.callback(
    Output("chat-input", "value"),
    Input("send-btn", "n_clicks"),
    State("chat-input", "value"),
    prevent_initial_call=True
)
def on_send(n_clicks, value):
    if value and value.strip():
        threading.Thread(target=send_message, args=(value.strip(),)).start()
    return ""

# Callback для создания цели
@app.callback(
    Output("create-goal-output", "children"),
    Input("create-goal-btn", "n_clicks"),
    State("goal-title", "value"),
    State("goal-desc", "value"),
    State("goal-priority", "value"),
    State("goal-due", "date"),
    State("goal-actor", "value"),
    State("goal-sphere", "value"),
    State("goal-parent", "value"),
    State("goal-tags", "value"),
    prevent_initial_call=True
)
def create_goal(n_clicks, title, desc, priority, due, actor, sphere, parent, tags):
    if not title:
        return html.Div("❌ Название обязательно", style={"color": "red", "textAlign": "center"})
    
    # TODO: отправить в Goals Service
    logger.info(f"Creating goal: {title}, actor={actor}, sphere={sphere}")
    
    return html.Div(f"✅ Цель '{title}' создана!", style={"color": "green", "textAlign": "center"})

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)