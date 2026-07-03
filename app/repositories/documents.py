from datetime import datetime

from app.db.database import get_connection


class DocumentRepository:
    def add_document(
        self,
        user_id: int,
        filename: str,
        content_type: str | None,
        extracted_text: str,
        summary: str | None = None,
    ) -> dict:
        conn = get_connection()
        cur = conn.cursor()
        created_at = datetime.utcnow().isoformat()

        cur.execute(
            """
            INSERT INTO documents (user_id, filename, content_type, extracted_text, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, filename, content_type, extracted_text, summary, created_at),
        )
        conn.commit()
        doc_id = cur.lastrowid

        cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row)

    def list_documents(self, user_id: int) -> list[dict]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM documents
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_latest_documents_text(self, user_id: int, limit: int = 3) -> str:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT filename, extracted_text
            FROM documents
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()
        conn.close()

        parts = []
        for row in rows:
            parts.append(f"Document: {row['filename']}\n{row['extracted_text'][:4000]}")
        return "\n\n".join(parts)