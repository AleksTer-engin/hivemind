# pages/goals.py
import dash
from dash import dcc, html, Input, Output, State, callback, register_page
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

register_page(__name__, path="/goals")

# Тестовые данные (потом заменим на API)
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

layout = html.Div([
    html.H1("🎯 Цели и задачи", style={"textAlign": "center", "marginBottom": "30px"}),
    
    # Вкладки
    dcc.Tabs([
        dcc.Tab(label="📋 Список целей", children=[
            html.Div(goals_list_layout(), style={"padding": "20px"})
        ]),
        dcc.Tab(label="🌳 Дерево целей", children=[
            html.Div(goal_tree_layout(), style={"padding": "20px"})
        ]),
        dcc.Tab(label="📊 Доска задач", children=[
            html.Div(task_board_layout(), style={"padding": "20px"})
        ]),
        dcc.Tab(label="➕ Новая цель", children=[
            html.Div(new_goal_layout(), style={"padding": "20px"})
        ])
    ])
])

def goals_list_layout():
    """Список целей (как в Todoist)"""
    return html.Div([
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
                    html.Input(type="checkbox", id=f"check_{g['id']}", style={"marginRight": "10px"}),
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
    ])

def goal_tree_layout():
    """Дерево целей"""
    # Данные для дерева
    tree_data = {
        "name": "HiveMind",
        "children": [
            {
                "name": "Фаза 1: Фундамент",
                "children": [
                    {"name": "API Gateway", "value": 100},
                    {"name": "Classifier", "value": 100},
                    {"name": "Базы данных", "value": 100}
                ]
            },
            {
                "name": "Фаза 2: Интеллект",
                "children": [
                    {"name": "Embedder", "value": 80},
                    {"name": "Linker", "value": 70},
                    {"name": "Goals Service", "value": 40}
                ]
            }
        ]
    }
    
    # Создаём treemap
    fig = go.Figure(go.Treemap(
        labels=['HiveMind', 'Фаза 1', 'API Gateway', 'Classifier', 'Базы данных',
                'Фаза 2', 'Embedder', 'Linker', 'Goals Service'],
        parents=['', 'HiveMind', 'Фаза 1', 'Фаза 1', 'Фаза 1',
                'HiveMind', 'Фаза 2', 'Фаза 2', 'Фаза 2'],
        values=[0, 0, 100, 100, 100, 0, 80, 70, 40],
        textinfo="label+value+percent parent",
        marker=dict(colors=['lightblue', 'lightgreen', 'gold', 'gold', 'gold',
                           'lightgreen', 'orange', 'orange', 'orange'])
    ))
    
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    
    return html.Div([
        dcc.Graph(figure=fig),
        html.Div([
            html.Span("🟢 Завершено", style={"marginRight": "20px"}),
            html.Span("🟡 В процессе", style={"marginRight": "20px"}),
            html.Span("🔴 Начато", style={"marginRight": "20px"})
        ], style={"marginTop": "20px", "textAlign": "center"})
    ])

def task_board_layout():
    """Доска задач (Trello-like)"""
    return html.Div([
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
    ])

def new_goal_layout():
    """Форма создания новой цели"""
    return html.Div([
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
    ])

# Callback для создания цели
@callback(
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
    
    return html.Div(f"✅ Цель '{title}' создана!", style={"color": "green", "textAlign": "center"})