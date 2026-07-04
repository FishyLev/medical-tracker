from datetime import datetime

from app.db.database import get_connection


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

    def get_session_summaries(self, user_id: int) -> list[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    session_id,
                    COUNT(*) AS message_count,
                    MIN(created_at) AS first_message_at,
                    MAX(created_at) AS last_message_at
                FROM conversations
                WHERE user_id = ?
                GROUP BY session_id
                ORDER BY MAX(created_at) DESC
                """,
                (user_id,),
            ).fetchall()

            return [
                {
                    "session_id": row["session_id"],
                    "message_count": row["message_count"],
                    "first_message_at": row["first_message_at"],
                    "last_message_at": row["last_message_at"],
                }
                for row in rows
            ]
        finally:
            conn.close()

    def delete_user_conversations(self, user_id: int) -> int:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM conversations WHERE user_id = ?",
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()