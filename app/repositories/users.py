from datetime import datetime

from app.db.sqlite import get_connection


class UserRepository:
    def create_user(self, name: str, age: int | None, gender: str | None, preferences: str | None) -> dict:
        conn = get_connection()
        try:
            created_at = datetime.utcnow().isoformat()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (name, age, gender, preferences, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, age, gender, preferences, created_at),
            )
            conn.commit()
            user_id = cursor.lastrowid

            row = conn.execute(
                "SELECT id, name, age, gender, preferences, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

            return {
                "user_id": row["id"],
                "name": row["name"],
                "age": row["age"],
                "gender": row["gender"],
                "preferences": row["preferences"],
                "created_at": row["created_at"],
            }
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> dict | None:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT id, name, age, gender, preferences, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()

            if not row:
                return None

            return {
                "user_id": row["id"],
                "name": row["name"],
                "age": row["age"],
                "gender": row["gender"],
                "preferences": row["preferences"],
                "created_at": row["created_at"],
            }
        finally:
            conn.close()