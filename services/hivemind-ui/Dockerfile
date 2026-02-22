FROM python:3.12-slim

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы зависимостей
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем код
COPY hivemind_ui/ ./hivemind_ui/

# Запускаем
CMD ["python", "-m", "hivemind_ui.main"]