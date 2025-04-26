FROM python:3.9-slim

WORKDIR /app

# Установка curl для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements.txt для лучшего кеширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем только необходимые файлы приложения вместо всего контекста
COPY app.py .

# Используем более эффективный запуск для uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]