import sys
import os
import time

sys.path.append(os.path.dirname(__file__))

def wait_for_redis(max_retries=30, delay=1):
    """Ожидание запуска Redis"""
    try:
        import redis
        for i in range(max_retries):
            try:
                r = redis.Redis(
                    host='redis',
                    port=6379,
                    password='music_shop_2024',
                    decode_responses=True
                )
                r.ping()
                print("✓ Redis подключен успешно")
                return True
            except Exception as e:
                if i == 0:
                    print(f"Ожидание Redis... ({max_retries} попыток)")
                print(f"  Попытка {i+1}/{max_retries}: {e}")
                time.sleep(delay)
        print("✗ Не удалось подключиться к Redis")
        return False
    except ImportError:
        print("Redis клиент не установлен, продолжаем без Redis")
        return True

def main():
    # Ждем запуск Redis
    if not wait_for_redis():
        print("Запуск без Redis поддержки")
    
    try:
        from app.music_shop import main as app_main
        print("Приложение запускается...")
        app_main()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

