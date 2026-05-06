import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_db
from models import Base, User, Pereval, Coord, Level, Images
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user(db_session):
    """Тест: создание пользователя"""
    user = User(email="test@test.com", phone="+123", fam="Test", name="User")
    db_session.add(user)
    db_session.commit()

    found = db_session.query(User).filter(User.email == "test@test.com").first()
    assert found is not None
    assert found.phone == "+123"


def test_create_pereval_with_relations(db_session):
    """Тест: создание перевала со всеми связями"""
    user = User(email="pereval@test.com", phone="+1", fam="Fam", name="Name")
    db_session.add(user)
    db_session.flush()

    coords = Coord(latitude=55.0, longitude=37.0)
    db_session.add(coords)
    db_session.flush()

    level = Level(winter="2A")
    db_session.add(level)
    db_session.flush()

    pereval = Pereval(
        beauty_title="пер.",
        title="Test Pass",
        add_time=datetime.now(),
        user_id=user.id,
        coord_id=coords.id,
        level_id=level.id
    )
    db_session.add(pereval)
    db_session.commit()

    assert pereval.id is not None
    assert pereval.user.email == "pereval@test.com"
    assert pereval.coord.latitude == 55.0


def test_unique_email_constraint(db_session):
    """Тест: уникальность email"""
    user1 = User(email="unique@test.com", phone="+1", fam="Fam1", name="Name1")
    user2 = User(email="unique@test.com", phone="+2", fam="Fam2", name="Name2")
    db_session.add(user1)
    db_session.commit()

    with pytest.raises(Exception):
        db_session.add(user2)
        db_session.commit()