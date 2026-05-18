#!/bin/bash
echo "[*] Starting Telegram Bot Engine..."

# Переходимо в директорію, де лежить сам скрипт (критично для серверів)
cd "$(dirname "$0")"

# Активуємо середовище та запускаємо
source venv/bin/activate
python main.py