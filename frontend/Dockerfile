FROM python:3.9-slim

WORKDIR /app

# Копируем только requirements.txt для лучшего кеширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем только необходимый файл приложения вместо всего контекста
COPY app.py .

EXPOSE 8501

# Параметры для уменьшения потребления ресурсов
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]