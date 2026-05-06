"""
Миграция для улучшения структуры БД:
- Добавление индексов
- Добавление CHECK-constraints
- Добавление полей created_at/updated_at
"""

from sqlalchemy import text
from database import engine


def run_migration():
    with engine.connect() as conn:
        # Добавляем поля created_at, updated_at
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception as e:
            print(f"users: {e}")

        try:
            conn.execute(text("ALTER TABLE coords ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception as e:
            print(f"coords: {e}")

        try:
            conn.execute(text("ALTER TABLE levels ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception as e:
            print(f"levels: {e}")

        try:
            conn.execute(text("ALTER TABLE pereval ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            conn.execute(text("ALTER TABLE pereval ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception as e:
            print(f"pereval: {e}")

        try:
            conn.execute(text("ALTER TABLE images ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        except Exception as e:
            print(f"images: {e}")

        # Добавляем индексы
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_email ON users (email)",
            "CREATE INDEX IF NOT EXISTS idx_coords_location ON coords (latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_pereval_user_status ON pereval (user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_pereval_add_time ON pereval (add_time)",
            "CREATE INDEX IF NOT EXISTS idx_images_pereval ON images (pereval_id)",
        ]
        for idx in indexes:
            try:
                conn.execute(text(idx))
                print(f"Index created: {idx}")
            except Exception as e:
                print(f"Error creating index: {e}")

        # Добавляем CHECK-constraints
        constraints = [
            "ALTER TABLE coords ADD CONSTRAINT check_latitude CHECK (latitude BETWEEN -90 AND 90)",
            "ALTER TABLE coords ADD CONSTRAINT check_longitude CHECK (longitude BETWEEN -180 AND 180)",
            "ALTER TABLE pereval ADD CONSTRAINT check_status CHECK (status IN ('new', 'pending', 'accepted', 'rejected'))",
        ]
        for constr in constraints:
            try:
                conn.execute(text(constr))
                print(f"Constraint added: {constr}")
            except Exception as e:
                print(f"Error adding constraint: {e}")

        conn.commit()
        print("Migration completed successfully.")


if __name__ == "__main__":
    run_migration()