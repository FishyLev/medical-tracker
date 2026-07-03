from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_connection
from app.models.api import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _validate_password_bytes(password: str) -> None:
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must be 72 bytes or fewer.",
        )


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    _validate_password_bytes(payload.password)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM users WHERE email = ?", (payload.email,))
        existing_user = cur.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(payload.password)
        created_at = datetime.utcnow().isoformat()

        cur.execute(
            """
            INSERT INTO users (name, age, gender, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name,
                payload.age,
                payload.gender,
                payload.email,
                hashed,
                created_at,
            ),
        )
        conn.commit()
        user_id = cur.lastrowid

    finally:
        conn.close()

    token = create_access_token({"sub": str(user_id)})
    return TokenResponse(access_token=token, user_id=user_id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    _validate_password_bytes(payload.password)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM users WHERE email = ?", (payload.email,))
        row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(row["id"])})
    return TokenResponse(access_token=token, user_id=row["id"])