from datetime import datetime

from app.db.sqlite import get_connection


class ConversationRepository:
    def add_message(self, user_id: int, session_id: str, role: str, message: str) -> None:
        conn = get_connection()
        try:
            created_at = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT INTO conversations (user_id, session_id, role, message, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, session_id, role, message, created_at),
            )
            conn.commit()
        finally:
            conn.close()

    def get_user_conversations(self, user_id: int) -> list[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, user_id, session_id, role, message, created_at
                FROM conversations
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()

            return [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "message": row["message"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        finally:
            conn.close()