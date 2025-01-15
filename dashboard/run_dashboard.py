import subprocess
import time

def run_metabase():
    # Проверяем, существует ли контейнер Metabase
    print("Проверка состояния контейнера Metabase...")

    # Проверяем наличие контейнера Metabase
    result = subprocess.run(["docker-compose", "ps", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.stdout:
        print("Контейнер Metabase уже существует, запускаем его...")
    else:
        print("Контейнер Metabase не найден, создаем и запускаем новый...")

    # Стартуем контейнер с Metabase или перезапускаем, если он существует
    subprocess.run(["docker-compose", "up", "--build", "-d"])

    # Даем время для того, чтобы Metabase запустился
    time.sleep(10)  # Подождать 10 секунд

    print("Metabase должен быть доступен по адресу http://localhost:3000")

if __name__ == "__main__":
    run_metabase()
