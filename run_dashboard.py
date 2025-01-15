import subprocess
import time

def run_metabase():
    # Стартуем контейнер с Metabase
    print("Запуск Metabase...")
    subprocess.run(["docker-compose", "up", "-d"])

    # Даем время для того, чтобы Metabase запустился
    time.sleep(10)  # Подождать 10 секунд

    print("Metabase должен быть доступен по адресу http://localhost:3000")

if __name__ == "__main__":
    run_metabase()
