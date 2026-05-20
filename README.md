# Список команд для работы с проектом
## В первую очередь скачайте зависимости! Так же нужно установить виртуальную среду (venv), если она не установлена.

``pip install -r requirements.txt`` - скачивание зависимостей проекта

``python3 manage.py runserver`` - запуск сервера, а следовательно и сайта

``python3 manage.py test`` - запуск тестирования проекта при помощи Django Test Framework

``python3 manage.py createsuperuser`` - создать администратора в базу данных.

``python3 manage.py migrate`` - применить файлы миграций на базу данных

``python3 manage.py migrate`` - создать файлы миграций для базы данных из models.py
