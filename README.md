# Event-extraction

# Пакеты для питона
* psycopg2
* flask-wtf
* flask_nav

# Создание базы данных
psql postgres -f create.sql 

# Загрузка статей
python3 spacy_event_extractor.py 

# Запуск сервера
python3 run_web_server.py 
