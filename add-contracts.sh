#!/usr/bin/env bash
# add-contracts.sh — добавить контракты для HiveMind
# Версия: 1.0
# Использование: ./add-contracts.sh [путь_к_hivemind]

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info()    { echo -e "${BLUE}🔍 $1${NC}"; }
print_section() { echo -e "\n${PURPLE}📋 $1${NC}"; }
print_error()   { echo -e "${RED}❌ $1${NC}"; }

# ==========================================
# Путь к проекту
# ==========================================
PROJECT_PATH="${1:-/home/welem/hivemind}"
PROJECT_PATH="${PROJECT_PATH%/}"

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}📜 Астролябия: добавление контрактов в HiveMind${NC}"
echo -e "${CYAN}📁 $PROJECT_PATH${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

# Проверка существования
if [ ! -d "$PROJECT_PATH" ]; then
    print_error "Папка не существует: $PROJECT_PATH"
    exit 1
fi

# ==========================================
# Создание папки contracts
# ==========================================
print_section "Создание структуры контрактов"

mkdir -p "$PROJECT_PATH/contracts"/{services,api,events,data,cells}
print_success "Папка contracts/ создана"

# ==========================================
# Контракт для api-gateway
# ==========================================
print_info "Создание контракта для api-gateway..."

cat > "$PROJECT_PATH/contracts/services/api-gateway.yaml" << 'EOF'
# Контракт сервиса api-gateway
# Версия: 1.0.0
# Статус: active

service:
  name: api-gateway
  language: go
  version: 1.0.0
  description: "Входная точка API, маршрутизация запросов к сервисам"

team:
  owner: "welem"
  slack: "#hivemind-gateway"

business_goals:
  - "Обеспечить единую точку входа для всех клиентов"
  - "Скрыть внутреннюю структуру микросервисов"
  - "Собирать метрики использования"

product_goals:
  - "Пользователь может загружать документы через API"
  - "Пользователь может искать похожие документы"
  - "Пользователь может видеть граф связей"

interfaces:
  rest:
    port: 8080
    endpoints:
      - path: /api/v1/documents
        method: POST
        description: "Загрузить документ"
        contract_ref: "../api/ingest.yaml"
      
      - path: /api/v1/documents/{id}
        method: GET
        description: "Получить документ"
        contract_ref: "../api/get-document.yaml"
      
      - path: /api/v1/documents/{id}/similar
        method: GET
        description: "Найти похожие"
        contract_ref: "../api/similar.yaml"
      
      - path: /api/v1/graph/{id}
        method: GET
        description: "Получить граф связей"
        contract_ref: "../api/graph.yaml"
      
      - path: /api/v1/status
        method: GET
        description: "Статус системы"
        contract_ref: "../api/status.yaml"

events:
  publishes:
    - topic: "document.ingest"
      description: "Новый документ для обработки"
      contract_ref: "../events/document-ingest.yaml"
  
  subscribes: []

dependencies:
  services:
    - name: classifier
      reason: "Для классификации документов"
    - name: embedder
      reason: "Для создания эмбеддингов"
    - name: linker
      reason: "Для установления связей"
  
  infrastructure:
    - nats (для публикации событий)
    - redis (для кэширования)

deployment:
  dockerfile: "../../services/api-gateway/Dockerfile"
  ports:
    - "8080:8080"
  environment:
    - NATS_URL
    - REDIS_URL
    - LOG_LEVEL
  healthcheck:
    command: "curl -f http://localhost:8080/health || exit 1"
    interval: "30s"
    timeout: "10s"
    retries: 3

testing:
  unit: true
  integration: true
  e2e: true
  performance_target: "1000 rps"

monitoring:
  metrics: "/metrics"
  logs: "stdout"
  tracing: "jaeger"

issues:
  known:
    - "Нет rate limiting"
    - "Нет аутентификации"
  
  todo:
    - "Добавить OpenAPI spec"
    - "Добавить request-id для трейсинга"
EOF

print_success "contracts/services/api-gateway.yaml создан"

# ==========================================
# Контракт для classifier
# ==========================================
print_info "Создание контракта для classifier..."

cat > "$PROJECT_PATH/contracts/services/classifier.yaml" << 'EOF'
# Контракт сервиса classifier
# Версия: 1.0.0
# Статус: active

service:
  name: classifier
  language: python
  version: 1.0.0
  description: "Классификация текстов, определение тегов"

team:
  owner: "welem"
  slack: "#hivemind-ml"

business_goals:
  - "Автоматически категоризировать входящую информацию"
  - "Уменьшить ручную работу по тегированию"

product_goals:
  - "Пользователь получает автоматические теги для документов"
  - "Можно искать по тегам"

inputs:
  - name: text
    type: string
    description: "Текст для классификации"
    required: true
    example: "Искусственный интеллект в медицине"
  
  - name: model
    type: string
    description: "Модель для классификации"
    required: false
    default: "default"
    options: ["default", "multilingual", "custom"]

outputs:
  - name: tags
    type: array
    items: string
    description: "Определённые теги"
    example: ["AI", "healthcare", "research"]
  
  - name: confidence
    type: float
    description: "Уверенность классификации (0-1)"
    example: 0.95
  
  - name: processing_time_ms
    type: integer
    description: "Время обработки в миллисекундах"

events:
  subscribes:
    - topic: "document.ingest"
      description: "Новый документ для классификации"
  
  publishes:
    - topic: "document.classified"
      description: "Документ классифицирован"
      contract_ref: "../events/document-classified.yaml"

dependencies:
  libraries:
    - transformers==4.35.0
    - torch==2.1.0
    - fastapi
    - nats-py
  
  services: []
  
  infrastructure:
    - nats (для получения/отправки событий)
    - postgres (для сохранения результатов)

deployment:
  dockerfile: "../../services/classifier/Dockerfile"
  ports:
    - "8081:8080"  # внутренний порт для debug
  environment:
    - MODEL_NAME=all-MiniLM-L6-v2
    - NATS_URL
    - DATABASE_URL
    - BATCH_SIZE=32
  replicas: 2
  resources:
    cpu: "1.0"
    memory: "2Gi"
    gpu: optional

testing:
  unit: true
  integration: true
  model_accuracy: "> 0.85"

files:
  required:
    - path: "src/main.py"
      purpose: "Точка входа"
    - path: "src/models/classifier.py"
      purpose: "Логика классификации"
    - path: "Dockerfile"
      purpose: "Контейнеризация"
  missing:
    - "tests/test_accuracy.py"

issues:
  known:
    - "Медленная загрузка моделей при старте"
  
  todo:
    - "Добавить кэширование моделей"
    - "Оптимизировать для GPU"
EOF

print_success "contracts/services/classifier.yaml создан"

# ==========================================
# Контракт для embedder (шаблон)
# ==========================================
print_info "Создание шаблона для embedder..."

cat > "$PROJECT_PATH/contracts/services/embedder.yaml" << 'EOF'
# Контракт сервиса embedder
# Версия: 0.1.0
# Статус: planned

service:
  name: embedder
  language: python  # или go?
  version: 0.1.0
  description: "Создание векторных эмбеддингов для текстов"

team:
  owner: "welem"
  slack: "#hivemind-ml"

business_goals:
  - "Обеспечить семантический поиск по документам"
  - "Находить похожие идеи независимо от формулировки"

product_goals:
  - "Пользователь может искать по смыслу, а не по ключевым словам"
  - "Система автоматически связывает похожие документы"

inputs:
  - name: text
    type: string
    description: "Текст для создания эмбеддинга"
    required: true
  
  - name: model
    type: string
    description: "Модель эмбеддинга"
    required: false
    default: "sentence-transformers/all-MiniLM-L6-v2"

outputs:
  - name: embedding
    type: array
    items: float
    description: "Векторное представление"
    length: 384  # для MiniLM
  
  - name: model
    type: string
    description: "Использованная модель"
  
  - name: dimension
    type: integer
    description: "Размерность вектора"

events:
  subscribes:
    - topic: "document.classified"
      description: "Классифицированный документ для эмбеддинга"
  
  publishes:
    - topic: "document.embedded"
      description: "Эмбеддинг создан"
      contract_ref: "../events/document-embedded.yaml"

dependencies:
  libraries:
    - sentence-transformers
    - torch
    - numpy
    - nats-py
  
  infrastructure:
    - nats
    - qdrant (для хранения эмбеддингов)

deployment:
  dockerfile: "../../services/embedder/Dockerfile"
  environment:
    - MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
    - NATS_URL
    - QDRANT_URL
    - BATCH_SIZE=64
  resources:
    cpu: "2.0"
    memory: "4Gi"
    gpu: recommended

testing:
  unit: false
  integration: false
  accuracy_target: "> 0.9 на тестовом наборе"

files:
  required:
    - path: "src/main.py"
      purpose: "Точка входа (TODO)"
    - path: "src/embedder.py"
      purpose: "Логика создания эмбеддингов (TODO)"
    - path: "Dockerfile"
      purpose: "Контейнеризация (TODO)"
  existing: []

issues:
  todo:
    - "Выбрать язык (Python с transformers или Go с готовыми моделями)"
    - "Определить размерность эмбеддингов"
    - "Решить, хранить ли эмбеддинги в Qdrant или отдельно"
    - "Написать тесты на качество"
EOF

print_success "contracts/services/embedder.yaml создан (шаблон)"

# ==========================================
# Контракт для linker (шаблон)
# ==========================================
print_info "Создание шаблона для linker..."

cat > "$PROJECT_PATH/contracts/services/linker.yaml" << 'EOF'
# Контракт сервиса linker
# Версия: 0.1.0
# Статус: planned

service:
  name: linker
  language: go  # для производительности при обходе графа
  version: 0.1.0
  description: "Установление связей между документами на основе эмбеддингов и метаданных"

team:
  owner: "welem"
  slack: "#hivemind-core"

business_goals:
  - "Создать сеть знаний, где идеи связаны естественным образом"
  - "Обнаруживать неочевидные связи между документами"

product_goals:
  - "Пользователь видит, как связаны его заметки"
  - "Можно навигировать по графу знаний"
  - "Система предлагает связанные документы"

inputs:
  - name: document_id
    type: string
    description: "ID документа для линковки"
    required: true
  
  - name: embedding_id
    type: string
    description: "ID эмбеддинга (опционально)"
    required: false
  
  - name: threshold
    type: float
    description: "Порог сходства для создания связи (0-1)"
    required: false
    default: 0.7

outputs:
  - name: links
    type: array
    items:
      type: object
      properties:
        target_id: string
        similarity: float
        link_type: string  # "similar", "references", "opposite"
    description: "Найденные связи"

events:
  subscribes:
    - topic: "document.embedded"
      description: "Новый эмбеддинг для линковки"
  
  publishes:
    - topic: "document.linked"
      description: "Связи созданы"
      contract_ref: "../events/document-linked.yaml"

dependencies:
  libraries:
    - github.com/neo4j/neo4j-go-driver/v5
    - github.com/nats-io/nats.go
  
  services: []
  
  infrastructure:
    - nats
    - neo4j (графовая БД)
    - qdrant (для поиска похожих векторов)

deployment:
  dockerfile: "../../services/linker/Dockerfile"
  environment:
    - NATS_URL
    - NEO4J_URL
    - QDRANT_URL
    - SIMILARITY_THRESHOLD=0.7
    - MAX_LINKS_PER_DOC=100
  resources:
    cpu: "1.0"
    memory: "2Gi"

testing:
  unit: false
  integration: false
  performance_target: "1000 документов/сек"

algorithms:
  similarity:
    - "косинусная близость для векторов"
    - "Jaccard для тегов"
  graph:
    - "поиск в ширину для связанных документов"
    - "PageRank для важности"

files:
  required:
    - path: "cmd/linker/main.go"
      purpose: "Точка входа (TODO)"
    - path: "internal/linker/linker.go"
      purpose: "Основная логика (TODO)"
    - path: "internal/store/neo4j.go"
      purpose: "Работа с графовой БД (TODO)"
    - path: "Dockerfile"
      purpose: "Контейнеризация (TODO)"
  existing: []

issues:
  todo:
    - "Выбрать алгоритм поиска похожих векторов"
    - "Определить типы связей"
    - "Решить, как обновлять связи при добавлении новых документов"
    - "Оптимизировать запросы к Neo4j"
EOF

print_success "contracts/services/linker.yaml создан (шаблон)"

# ==========================================
# Контракт для hivemind-ui
# ==========================================
print_info "Создание контракта для hivemind-ui..."

cat > "$PROJECT_PATH/contracts/services/hivemind-ui.yaml" << 'EOF'
# Контракт сервиса hivemind-ui
# Версия: 1.0.0
# Статус: active

service:
  name: hivemind-ui
  language: python
  version: 1.0.0
  description: "Веб-интерфейс для взаимодействия с HiveMind"

team:
  owner: "welem"
  slack: "#hivemind-ui"

business_goals:
  - "Дать пользователю удобный доступ к возможностям HiveMind"
  - "Визуализировать граф знаний"

product_goals:
  - "Пользователь может загружать документы через интерфейс"
  - "Пользователь видит граф связей"
  - "Пользователь может искать по документам"

interfaces:
  web:
    port: 8501
    type: streamlit
    pages:
      - path: "/"
        name: "Загрузка"
      - path: "/graph"
        name: "Граф знаний"
      - path: "/search"
        name: "Поиск"
      - path: "/status"
        name: "Статус системы"

dependencies:
  services:
    - name: api-gateway
      reason: "Все запросы идут через gateway"
  
  libraries:
    - streamlit==1.28.0
    - httpx==0.25.0
    - pandas==2.1.0
    - plotly==5.18.0
    - networkx==3.1 (для визуализации графа)

deployment:
  dockerfile: "../../services/hivemind-ui/Dockerfile"
  ports:
    - "8501:8501"
  environment:
    - API_GATEWAY_URL=http://api-gateway:8080
    - NATS_URL (опционально, для прямого доступа)

testing:
  unit: false
  e2e: true

files:
  required:
    - path: "app.py"
      purpose: "Точка входа Streamlit"
    - path: "pages/graph.py"
      purpose: "Страница с графом"
    - path: "pages/search.py"
      purpose: "Страница поиска"
    - path: "utils/api_client.py"
      purpose: "Клиент для API Gateway"
  existing:
    - "app.py"
EOF

print_success "contracts/services/hivemind-ui.yaml создан"

# ==========================================
# API-контракты
# ==========================================
print_section "Создание API-контрактов"

# ingest.yaml
cat > "$PROJECT_PATH/contracts/api/ingest.yaml" << 'EOF'
# Контракт: загрузка документа
# Метод: POST /api/v1/documents

request:
  body:
    required:
      - content
    properties:
      content:
        type: string
        description: "Текст документа"
        example: "Искусственный интеллект в медицине"
      metadata:
        type: object
        description: "Метаданные документа"
        properties:
          source:
            type: string
            example: "web"
          tags:
            type: array
            items: string
            example: ["AI", "draft"]

response:
  status: 202
  body:
    properties:
      id:
        type: string
        format: uuid
        description: "ID созданного документа"
      status:
        type: string
        enum: ["processing"]
      task_id:
        type: string
        format: uuid
        description: "ID задачи для отслеживания"

errors:
  400:
    description: "Неверный запрос (нет content)"
  413:
    description: "Слишком большой документ"
  429:
    description: "Слишком много запросов"
  503:
    description: "Сервис временно недоступен"
EOF

print_success "contracts/api/ingest.yaml создан"

# get-document.yaml
cat > "$PROJECT_PATH/contracts/api/get-document.yaml" << 'EOF'
# Контракт: получение документа
# Метод: GET /api/v1/documents/{id}

parameters:
  - name: id
    in: path
    required: true
    schema:
      type: string
      format: uuid

response:
  status: 200
  body:
    properties:
      id:
        type: string
        format: uuid
      content:
        type: string
      metadata:
        type: object
      embeddings:
        type: array
        items:
          type: string
          format: uuid
      links:
        type: array
        items:
          type: string
          format: uuid
      created_at:
        type: string
        format: date-time

errors:
  404:
    description: "Документ не найден"
EOF

print_success "contracts/api/get-document.yaml создан"

# similar.yaml
cat > "$PROJECT_PATH/contracts/api/similar.yaml" << 'EOF'
# Контракт: поиск похожих документов
# Метод: GET /api/v1/documents/{id}/similar

parameters:
  - name: id
    in: path
    required: true
    schema:
      type: string
      format: uuid
  - name: limit
    in: query
    schema:
      type: integer
      default: 10
      maximum: 100
  - name: threshold
    in: query
    schema:
      type: number
      format: float
      default: 0.7
      minimum: 0
      maximum: 1

response:
  status: 200
  body:
    properties:
      documents:
        type: array
        items:
          type: object
          properties:
            id:
              type: string
              format: uuid
            similarity:
              type: number
              format: float
            content:
              type: string
              description: "Текст (обрезанный для экономии)"
      total:
        type: integer
EOF

print_success "contracts/api/similar.yaml создан"

# ==========================================
# Event-контракты
# ==========================================
print_section "Создание event-контрактов"

# document-classified.yaml
cat > "$PROJECT_PATH/contracts/events/document-classified.yaml" << 'EOF'
# Контракт события: document.classified
# Версия: 1.0.0

event:
  topic: "document.classified"
  version: "1.0.0"
  description: "Документ классифицирован"

payload:
  required:
    - document_id
    - tags
    - timestamp
  properties:
    document_id:
      type: string
      format: uuid
      description: "ID документа"
    tags:
      type: array
      items:
        type: string
      description: "Присвоенные теги"
    confidence:
      type: number
      format: float
      minimum: 0
      maximum: 1
      description: "Уверенность классификации"
    model:
      type: string
      description: "Модель, использованная для классификации"
    processing_time_ms:
      type: integer
      description: "Время обработки"
    timestamp:
      type: string
      format: date-time
      description: "Время события"

example:
  document_id: "123e4567-e89b-12d3-a456-426614174000"
  tags: ["AI", "healthcare", "research"]
  confidence: 0.95
  model: "multilingual-bert"
  processing_time_ms: 150
  timestamp: "2026-02-22T15:30:00Z"
EOF

print_success "contracts/events/document-classified.yaml создан"

# ==========================================
# README для контрактов
# ==========================================
print_section "Создание README для контрактов"

cat > "$PROJECT_PATH/contracts/README.md" << 'EOF'
# 📜 Контракты HiveMind

Это папка содержит **контракты** всех сервисов, API и событий HiveMind.

## 📁 Структура
contracts/
├── services/ # Контракты микросервисов
├── api/ # REST API контракты
├── events/ # NATS event контракты
├── data/ # Модели данных (soon)
└── cells/ # Контракты функций (soon)

text

## 🎯 Зачем это нужно

1. **Единый источник правды** — все знают, что должен делать каждый сервис
2. **Автоматическая проверка** — можно проверить, соответствует ли код контракту
3. **Документация** — новые разработчики понимают систему за 5 минут
4. **Генерация кода** — из контрактов можно генерировать клиенты и моки

## 📋 Статус сервисов

| Сервис | Статус | Контракт |
|--------|--------|----------|
| api-gateway | ✅ active | [services/api-gateway.yaml](services/api-gateway.yaml) |
| classifier | ✅ active | [services/classifier.yaml](services/classifier.yaml) |
| embedder | ⏳ planned | [services/embedder.yaml](services/embedder.yaml) |
| linker | ⏳ planned | [services/linker.yaml](services/linker.yaml) |
| hivemind-ui | ✅ active | [services/hivemind-ui.yaml](services/hivemind-ui.yaml) |

## 🔄 Жизненный цикл контракта

1. **Черновик (draft)** — идея, обсуждается
2. **В планах (planned)** — утверждён, но не реализован
3. **Активен (active)** — реализован и работает
4. **Устарел (deprecated)** — будет удалён
5. **Удалён (removed)** — больше не используется

## 🧪 Проверка контрактов

```bash
# TODO: скрипт проверки
./check-contracts.sh
Он будет проверять:

Существуют ли все файлы, указанные в контрактах

Соответствует ли Dockerfile путям

Есть ли необходимые переменные окружения

✍️ Как добавить новый контракт
Создать YAML-файл в соответствующей папке

Заполнить обязательные поля

Обновить этот README

Закоммитить

🌍 Языки
Контракты пишутся на русском (для нас) и английском (для мира).
Пока только русский, но планируется билингва.

Помните: Контракт — это обещание. Нарушать обещания — плохо. 😊
EOF

print_success "contracts/README.md создан"

#==========================================
# Обновление .gitignore
#==========================================
print_section "Обновление .gitignore"

cat >> "$PROJECT_PATH/.gitignore" << 'EOF'

Контракты (исключаем временные файлы)
contracts/.tmp
contracts/.swp
EOF

print_success ".gitignore обновлён"

#==========================================
# Итог
#==========================================
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Контракты успешно добавлены в HiveMind!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

echo -e "\n📁 Созданы файлы:"
find "$PROJECT_PATH/contracts" -type f -name ".yaml" -o -name ".md" | sed "s|$PROJECT_PATH/| |" | sort

echo -e "\n${YELLOW}👉 Теперь закоммить изменения:${NC}"
echo " cd $PROJECT_PATH"
echo " git add contracts/"
echo " git commit -m "feat: add service contracts for HiveMind""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

# Подсказка про embedder и linker
echo -e "\n${PURPLE}📌 Для embedder и linker созданы шаблоны контрактов.${NC}"
echo " Они помечены как 'planned' — можно начинать реализацию."
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
