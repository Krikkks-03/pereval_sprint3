from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Index, CheckConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_user_email', 'email'),
        {'comment': 'Таблица пользователей системы'}
    )

    id = Column(Integer, primary_key=True, index=True, comment='Первичный ключ')
    email = Column(String(255), unique=True, nullable=False, index=True, comment='Email пользователя')
    phone = Column(String(20), nullable=False, comment='Номер телефона')
    fam = Column(String(100), nullable=False, comment='Фамилия')
    name = Column(String(100), nullable=False, comment='Имя')
    otc = Column(String(100), nullable=True, comment='Отчество')
    created_at = Column(DateTime, default=datetime.now, comment='Дата регистрации')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='Дата обновления')

    perevals = relationship("Pereval", back_populates="user", cascade="all, delete-orphan")


class Coord(Base):
    __tablename__ = 'coords'
    __table_args__ = (
        CheckConstraint('latitude BETWEEN -90 AND 90', name='check_latitude'),
        CheckConstraint('longitude BETWEEN -180 AND 180', name='check_longitude'),
        Index('idx_coords_location', 'latitude', 'longitude'),
    )

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, comment='Широта (от -90 до 90)')
    longitude = Column(Float, nullable=False, comment='Долгота (от -180 до 180)')
    created_at = Column(DateTime, default=datetime.now)

    pereval = relationship("Pereval", back_populates="coord", uselist=False)


class Level(Base):
    __tablename__ = 'levels'

    id = Column(Integer, primary_key=True, index=True)
    winter = Column(String(10), nullable=True, comment='Категория сложности зимой (1A-3B)')
    summer = Column(String(10), nullable=True, comment='Категория сложности летом (1A-3B)')
    autumn = Column(String(10), nullable=True, comment='Категория сложности осенью (1A-3B)')
    spring = Column(String(10), nullable=True, comment='Категория сложности весной (1A-3B)')
    created_at = Column(DateTime, default=datetime.now)

    pereval = relationship("Pereval", back_populates="level", uselist=False)


class Pereval(Base):
    __tablename__ = 'pereval'
    __table_args__ = (
        Index('idx_pereval_user_status', 'user_id', 'status'),
        Index('idx_pereval_add_time', 'add_time'),
        CheckConstraint("status IN ('new', 'pending', 'accepted', 'rejected')", name='check_status'),
    )

    id = Column(Integer, primary_key=True, index=True)
    beauty_title = Column(String(100), nullable=False, comment='Красивое название (пер., пер.)')
    title = Column(String(200), nullable=False, comment='Название перевала')
    other_titles = Column(Text, nullable=True, comment='Альтернативные названия')
    connect = Column(Text, nullable=True, comment='Соединение с другими перевалами')
    add_time = Column(DateTime, nullable=False, comment='Время добавления')
    status = Column(String(20), default='new', nullable=False, comment='Статус модерации')

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    coord_id = Column(Integer, ForeignKey('coords.id', ondelete='CASCADE'), nullable=False, unique=True)
    level_id = Column(Integer, ForeignKey('levels.id', ondelete='CASCADE'), nullable=False, unique=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="perevals")
    coord = relationship("Coord", back_populates="pereval")
    level = relationship("Level", back_populates="pereval")
    images = relationship("Images", back_populates="pereval", cascade="all, delete-orphan")


class Images(Base):
    __tablename__ = 'images'
    __table_args__ = (
        Index('idx_images_pereval', 'pereval_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    pereval_id = Column(Integer, ForeignKey('pereval.id', ondelete='CASCADE'), nullable=False)
    data = Column(Text, nullable=False, comment='Фото в формате base64')
    title = Column(String(200), nullable=False, comment='Название/описание фото')
    created_at = Column(DateTime, default=datetime.now)

    pereval = relationship("Pereval", back_populates="images")