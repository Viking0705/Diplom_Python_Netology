# Дипломная работа по профессии "Python-разработчик" (базовый уровень)

• [Задание дипломного проекта](https://github.com/netology-code/python-final-diplom/tree/master)

• [Документация в Postman](https://www.postman.com/viking75/workspace/my-shop-workspace/documentation/34353063-55ab4fb9-35e3-4654-8117-f24a85ae015a)

• В файле ```.env```  заданы:

– для работы с базой данных: ```POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD```;

– для отправки email: ```EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL```.

#### Начало работы с проектом:
• Создаем и активируем виртуальную среду: ```python -m venv venv``` и ```.\venv\Scripts\activate```.

• Устанавливаем зависимости: ```pip install -r requirements.txt```.

• Создаем базу данных: ```createdb -U postgres my_shop```.

• Создаем и применяем миграции: ```python manage.py makemigrations``` и ```python manage.py migrate```.

• Запускаем сервер: ```python manage.py runserver```.

• Создаем суперпользователя: ```python manage.py createsuperuser```.