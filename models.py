from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    fam = Column(String, nullable=False)
    name = Column(String, nullable=False)
    otc = Column(String, nullable=True)
    perevals = relationship("Pereval", back_populates="user")

class Coord(Base):
    __tablename__ = 'coords'
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    pereval = relationship("Pereval", back_populates="coord")

class Level(Base):
    __tablename__ = 'levels'
    id = Column(Integer, primary_key=True, index=True)
    winter = Column(String, nullable=True)
    summer = Column(String, nullable=True)
    autumn = Column(String, nullable=True)
    spring = Column(String, nullable=True)
    pereval = relationship("Pereval", back_populates="level")

class Pereval(Base):
    __tablename__ = 'pereval'
    id = Column(Integer, primary_key=True, index=True)
    beauty_title = Column(String, nullable=False)
    title = Column(String, nullable=False)
    other_titles = Column(String, nullable=True)
    connect = Column(String, nullable=True)
    add_time = Column(DateTime, nullable=False)
    status = Column(String, default='new', nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    coord_id = Column(Integer, ForeignKey('coords.id'), nullable=False)
    level_id = Column(Integer, ForeignKey('levels.id'), nullable=False)
    user = relationship("User", back_populates="perevals")
    coord = relationship("Coord", back_populates="pereval")
    level = relationship("Level", back_populates="pereval")
    images = relationship("Images", back_populates="pereval")

class Images(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True, index=True)
    pereval_id = Column(Integer, ForeignKey('pereval.id'), nullable=False)
    data = Column(String, nullable=False)
    title = Column(String, nullable=False)
    pereval = relationship("Pereval", back_populates="images")