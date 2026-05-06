"""
Тесты для Pereval API Sprint 2
Запуск: pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from main import app
from database import get_db
from models import Base, Pereval, User, Coord, Level, Images

# ============================================================
# НАСТРОЙКА ТЕСТОВОЙ БАЗЫ ДАННЫХ (SQLite для изоляции)
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Переопределяем зависимость get_db для использования тестовой БД"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Подменяем оригинальную зависимость на тестовую
app.dependency_overrides[get_db] = override_get_db

# Создаём клиент для тестирования API (правильный способ)
client = TestClient(app)  # В новых версиях это работает, но если нет – используем другую форму


# ============================================================
# ФИКСТУРЫ (настройка перед каждым тестом)
# ============================================================

@pytest.fixture(autouse=True)
def setup_database():
    """Автоматически создаёт таблицы перед каждым тестом и удаляет после"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================
# ТЕСТЫ ДЛЯ POST /submitData (СОЗДАНИЕ ПЕРЕВАЛА)
# ============================================================

def test_create_pereval_success():
    """Тест 1: Успешное создание перевала"""
    response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Тестовый перевал",
        "other_titles": "Альтернативное название",
        "connect": "Соединение с другим перевалом",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "ivan@example.com",
            "phone": "+79123456789",
            "fam": "Иванов",
            "name": "Иван",
            "otc": "Иванович"
        },
        "coords": {
            "latitude": 55.7558,
            "longitude": 37.6176
        },
        "level": {
            "winter": "2A",
            "summer": "1B",
            "autumn": "2A",
            "spring": "1B"
        },
        "images": [
            {"data": "base64data123", "title": "Вид с севера"},
            {"data": "base64data456", "title": "Вид с юга"}
        ]
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["message"] == "Success"
    assert data["id"] is not None
    assert isinstance(data["id"], int)


def test_create_pereval_duplicate():
    """Тест 2: Попытка создать дубликат (такой же перевал у того же пользователя)"""
    # Данные для создания
    pereval_data = {
        "beauty_title": "пер.",
        "title": "Уникальный перевал",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "duplicate@example.com",
            "phone": "+79991112233",
            "fam": "Петров",
            "name": "Петр"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {"winter": "1A"},
        "images": []
    }

    # Первый запрос — должен успешно создаться
    response1 = client.post("/submitData", json=pereval_data)
    assert response1.json()["status"] == 200

    # Второй запрос с теми же данными — должен вернуть дубликат
    response2 = client.post("/submitData", json=pereval_data)
    assert response2.status_code == 200
    data = response2.json()
    assert data["status"] == 500
    assert data["message"] == "Duplicate entry"
    assert data["id"] is None


def test_create_pereval_existing_user():
    """Тест 3: Создание перевала для уже существующего пользователя (не создаём нового)"""
    # Сначала создаём пользователя через первый перевал
    response1 = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Первый перевал",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "existing@example.com",
            "phone": "+1122334455",
            "fam": "Сидоров",
            "name": "Сидор"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {},
        "images": []
    })
    assert response1.json()["status"] == 200

    # Создаём второй перевал с тем же email
    response2 = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Второй перевал",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "existing@example.com",  # Тот же email
            "phone": "+9999999999",  # Другой телефон (должен проигнорироваться)
            "fam": "ДругаяФамилия",  # Должен проигнорироваться
            "name": "ДругоеИмя"  # Должен проигнорироваться
        },
        "coords": {"latitude": 56.0, "longitude": 38.0},
        "level": {},
        "images": []
    })

    assert response2.status_code == 200
    data = response2.json()
    assert data["status"] == 200
    assert data["id"] is not None

    # Проверяем, что пользователь остался с исходными данными
    get_response = client.get(f"/submitData/{data['id']}")
    assert get_response.json()["user"]["email"] == "existing@example.com"
    assert get_response.json()["user"]["phone"] == "+1122334455"  # Остался старый телефон
    assert get_response.json()["user"]["fam"] == "Сидоров"


# ============================================================
# ТЕСТЫ ДЛЯ GET /submitData/{id} (ПОЛУЧЕНИЕ ПЕРЕВАЛА)
# ============================================================

def test_get_pereval_success():
    """Тест 4: Получение существующего перевала по ID"""
    # Сначала создаём перевал
    create_response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Перевал для получения",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "get@example.com",
            "phone": "+1",
            "fam": "GetFam",
            "name": "GetName"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {"winter": "3A", "summer": "2B"},
        "images": [{"data": "img123", "title": "Фото"}]
    })
    pereval_id = create_response.json()["id"]

    # Получаем перевал
    response = client.get(f"/submitData/{pereval_id}")
    assert response.status_code == 200
    data = response.json()

    # Проверяем все поля
    assert data["id"] == pereval_id
    assert data["beauty_title"] == "пер."
    assert data["title"] == "Перевал для получения"
    assert data["status"] == "new"
    assert data["user"]["email"] == "get@example.com"
    assert data["user"]["fam"] == "GetFam"
    assert data["coords"]["latitude"] == 55.0
    assert data["level"]["winter"] == "3A"
    assert len(data["images"]) == 1
    assert data["images"][0]["title"] == "Фото"


def test_get_pereval_not_found():
    """Тест 5: Получение несуществующего перевала (должен вернуть 404)"""
    response = client.get("/submitData/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Pereval not found"


# ============================================================
# ТЕСТЫ ДЛЯ PATCH /submitData/{id} (ОБНОВЛЕНИЕ ПЕРЕВАЛА)
# ============================================================

def test_update_pereval_success():
    """Тест 6: Успешное обновление перевала со статусом new"""
    # Создаём перевал
    create_response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Старое название",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "update@example.com",
            "phone": "+1",
            "fam": "UpdateFam",
            "name": "UpdateName"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {"winter": "1A"},
        "images": [{"data": "old_image", "title": "Старое фото"}]
    })
    pereval_id = create_response.json()["id"]

    # Обновляем только название и уровень
    response = client.patch(f"/submitData/{pereval_id}", json={
        "title": "Новое название",
        "level": {"winter": "3B", "summer": "2C"}
    })
    assert response.status_code == 200
    assert response.json()["state"] == 1
    assert response.json()["message"] == "Запись успешно обновлена"

    # Проверяем, что обновилось
    get_response = client.get(f"/submitData/{pereval_id}")
    assert get_response.json()["title"] == "Новое название"
    assert get_response.json()["level"]["winter"] == "3B"
    assert get_response.json()["level"]["summer"] == "2C"

    # Проверяем, что координаты и пользователь не изменились
    assert get_response.json()["coords"]["latitude"] == 55.0
    assert get_response.json()["user"]["email"] == "update@example.com"


def test_update_pereval_with_images():
    """Тест 7: Обновление фотографий (старые удаляются, добавляются новые)"""
    # Создаём перевал с 2 фото
    create_response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "С фото",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "images@example.com",
            "phone": "+1",
            "fam": "Fam",
            "name": "Name"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {},
        "images": [
            {"data": "img1", "title": "Фото 1"},
            {"data": "img2", "title": "Фото 2"}
        ]
    })
    pereval_id = create_response.json()["id"]

    # Обновляем фото — теперь 1 новое фото
    response = client.patch(f"/submitData/{pereval_id}", json={
        "images": [{"data": "new_img", "title": "Новое фото"}]
    })
    assert response.json()["state"] == 1

    # Проверяем, что старые фото удалились, добавилось новое
    get_response = client.get(f"/submitData/{pereval_id}")
    assert len(get_response.json()["images"]) == 1
    assert get_response.json()["images"][0]["title"] == "Новое фото"


def test_update_pereval_not_found():
    """Тест 8: Обновление несуществующего перевала"""
    response = client.patch("/submitData/99999", json={"title": "Новое"})
    assert response.status_code == 200
    assert response.json()["state"] == 0
    assert response.json()["message"] == "Запись не найдена"


def test_update_pereval_status_not_new():
    """Тест 9: Попытка обновить перевал со статусом не 'new' (должна быть ошибка)"""
    # Создаём перевал
    create_response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Нельзя обновить",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "moderated@example.com",
            "phone": "+1",
            "fam": "Fam",
            "name": "Name"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {},
        "images": []
    })
    pereval_id = create_response.json()["id"]

    # Меняем статус напрямую в БД (имитируем действия модератора)
    db = TestingSessionLocal()
    pereval = db.query(Pereval).filter(Pereval.id == pereval_id).first()
    pereval.status = "accepted"
    db.commit()
    db.close()

    # Пытаемся обновить
    response = client.patch(f"/submitData/{pereval_id}", json={"title": "Новое название"})
    assert response.status_code == 200
    assert response.json()["state"] == 0
    assert "Нельзя редактировать" in response.json()["message"]


# ============================================================
# ТЕСТЫ ДЛЯ GET /submitData?user_email= (ПЕРЕВАЛЫ ПОЛЬЗОВАТЕЛЯ)
# ============================================================

def test_get_user_perevals_success():
    """Тест 10: Получение списка всех перевалов пользователя"""
    email = "list_user@example.com"

    # Создаём 3 перевала для одного пользователя
    for i in range(3):
        client.post("/submitData", json={
            "beauty_title": "пер.",
            "title": f"Перевал {i}",
            "add_time": "2025-04-06T12:00:00",
            "user": {
                "email": email,
                "phone": "+1",
                "fam": "ListFam",
                "name": "ListName"
            },
            "coords": {"latitude": 55.0 + i, "longitude": 37.0 + i},
            "level": {"winter": f"{i}A"},
            "images": []
        })

    response = client.get(f"/submitData?user_email={email}")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["title"] in ["Перевал 0", "Перевал 1", "Перевал 2"]
    assert data[0]["status"] == "new"

    # Проверяем, что у каждого объекта есть нужные поля
    for item in data:
        assert "id" in item
        assert "title" in item
        assert "status" in item


def test_get_user_perevals_no_perevals():
    """Тест 11: Пользователь существует, но перевалов нет"""
    # Сначала создаём пользователя через перевал
    email = "empty@example.com"
    client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Единственный перевал",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": email,
            "phone": "+1",
            "fam": "Fam",
            "name": "Name"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {},
        "images": []
    })

    # Запрашиваем перевалы — должен быть 1
    response = client.get(f"/submitData?user_email={email}")
    assert len(response.json()) == 1


def test_get_user_perevals_user_not_found():
    """Тест 12: Пользователь не найден — возвращаем пустой список"""
    response = client.get("/submitData?user_email=notexist@example.com")
    assert response.status_code == 200
    assert response.json() == []


def test_get_user_perevals_invalid_email():
    """Тест 13: Передан пустой email (должен вернуть ошибку валидации)"""
    response = client.get("/submitData")
    assert response.status_code == 422


def test_create_pereval_minimal_data():
    """Тест 14: Создание перевала только с обязательными полями"""
    response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Минимальный перевал",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "minimal@example.com",
            "phone": "+1",
            "fam": "Min",
            "name": "Mal"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {},
        "images": []
    })
    assert response.status_code == 200
    assert response.json()["status"] == 200
    assert response.json()["id"] is not None


def test_update_pereval_partial_data():
    """Тест 15: Частичное обновление (только одно поле)"""
    create_response = client.post("/submitData", json={
        "beauty_title": "пер.",
        "title": "Оригинал",
        "add_time": "2025-04-06T12:00:00",
        "user": {
            "email": "partial@example.com",
            "phone": "+1",
            "fam": "Fam",
            "name": "Name"
        },
        "coords": {"latitude": 55.0, "longitude": 37.0},
        "level": {"winter": "1A"},
        "images": []
    })
    pereval_id = create_response.json()["id"]

    # Обновляем только одно поле
    response = client.patch(f"/submitData/{pereval_id}", json={"other_titles": "Новый альт. тайтл"})
    assert response.json()["state"] == 1

    get_response = client.get(f"/submitData/{pereval_id}")
    assert get_response.json()["other_titles"] == "Новый альт. тайтл"
    assert get_response.json()["title"] == "Оригинал"
    assert get_response.json()["level"]["winter"] == "1A"