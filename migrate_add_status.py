from database import engine
from sqlalchemy import text


def add_status_column():
    with engine.connect() as conn:
        # Проверяем, существует ли колонка
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='pereval' AND column_name='status'
        """))

        if result.fetchone() is None:
            conn.execute(text(
                "ALTER TABLE pereval ADD COLUMN status VARCHAR(50) DEFAULT 'new' NOT NULL"
            ))
            conn.commit()
            print("✅ Status column added successfully")
        else:
            print("ℹ️ Status column already exists")


if __name__ == "__main__":
    add_status_column()