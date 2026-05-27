#!/usr/bin/env bash
# Выход при любой ошибке внутри скрипта
set -o errexit

pip install -r requirements.txt

# Сборка статических файлов для WhiteNoise
python manage.py collectstatic --no-input

# Применение миграций к новой базе данных PostgreSQL
python manage.py migrate

# 4. ВРЕМЕННАЯ СТРОКА: Импорт ваших данных из SQLite в PostgreSQL
python manage.py loaddata data.json
