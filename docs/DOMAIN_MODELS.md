# МОДЕЛИ ДАННЫХ HIVEMIND

## 📦 **Базовые сущности**

### **Document** (документ)
```yaml
Document:
  id: UUID
  content: string
  metadata:
    source: string      # откуда пришёл
    created_at: timestamp
    author: string      # кто создал/загрузил
    tags: string[]      # теги (из классификатора)
  embeddings: Embedding[]  # связь с эмбеддингами
  links: Link[]         # связи с другими документами
Embedding (эмбеддинг)
yaml
Embedding:
  id: UUID
  document_id: UUID
  model: string         # какая модель создала
  version: string       # версия модели
  vector: float[]       # сам вектор (1536 для OpenAI, 384 для MiniLM)
  created_at: timestamp
Link (связь)
yaml
Link:
  id: UUID
  source_id: UUID       # откуда связь
  target_id: UUID       # куда связь
  type: string          # тип связи (references, similar, opposite, etc.)
  weight: float         # сила связи (0-1)
  created_at: timestamp
  metadata: {}          # дополнительные данные
Agent (агент)
yaml
Agent:
  id: UUID
  name: string
  type: string          # classifier, embedder, linker, etc.
  status: string        # active, idle, dead
  last_heartbeat: timestamp
  capabilities: string[]  # что умеет
  config: {}            # конфигурация агента
Task (задача)
yaml
Task:
  id: UUID
  type: string          # classify, embed, link, etc.
  input: {}             # входные данные
  output: {}            # выходные данные (после выполнения)
  status: string        # pending, processing, done, failed
  assigned_to: UUID     # какой агент выполняет
  created_at: timestamp
  completed_at: timestamp
  parent_task: UUID     # для цепочек задач
  subtasks: UUID[]      # подзадачи
🔗 Связи между сущностями
text
Document 1 ──┬── has ──► Embedding N
             ├── has ──► Link N (source)
             └── has ──► Link N (target)

Agent N ──► executes ──► Task N
Task N ──► processes ──► Document N
📊 Инварианты (бизнес-правила)
У каждого документа может быть несколько эмбеддингов (разные модели)

Связи всегда двусторонние (если A ссылается на B, то B автоматически имеет обратную связь)

Агент должен отправлять heartbeat каждые 30 секунд, иначе считается мёртвым

Задача не может быть назначена мёртвому агенту

Один документ не может иметь больше 1000 связей (защита от переполнения)
