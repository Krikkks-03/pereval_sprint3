import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Берём DATABASE_URL из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Если нет, собираем из отдельных (локальная разработка)
if not DATABASE_URL:
    DB_HOST = os.getenv("FSTR_DB_HOST")
    DB_PORT = os.getenv("FSTR_DB_PORT")
    DB_USER = os.getenv("FSTR_LOGIN")
    DB_PASS = os.getenv("FSTR_PASS")
    DB_NAME = os.getenv("FSTR_DB_NAME")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()