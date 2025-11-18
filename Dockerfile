# 1. Указываем базовый образ с Python
FROM python:3.11-slim

# Устанавливаем зависимости для Tkinter и X11
RUN apt-get update && apt-get install -y \
    python3-tk \
    tk \
    tcl \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Создаем директории для данных и логов
RUN mkdir -p /app/data /app/logs


# 2. Устанавливаем рабочий каталог внутри контейнера
WORKDIR /app

# 3. Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Копируем остальной код проекта в рабочий каталог
COPY . .


# 5. Указываем команду для запуска приложения при старте контейнера
CMD ["python3", "run_app.py"]
