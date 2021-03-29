# API службы доставки
* ##### Решение задания для Yandex Beckend School

# Требования
* ##### Python 3.6+
* ##### Flask 
* ##### Настроенный venv

# Запуск сайта
1. ##### Открыть корень проетка через консоль
2. ##### Выполнить следующие команды:
    * `sudo service nginx restart`
    * `sudo systemctl restart gunicorn.service`
    * `sudo systemctl enable gunicorn.service`
    * `sudo systemctl start gunicorn.service`
    * `sudo systemctl status gunicorn.service`

# Запуск тестирования
1. ##### Открыть корень проетка через консоль
2. ##### Выполнить слудующую команду:
    * `pytest`

# Запуск проверки на `pep8`
1. ##### Открыть корень проетка через консоль
2. ##### Выполнить слудующую команду:
    * `flake8`