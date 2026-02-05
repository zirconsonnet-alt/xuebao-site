import hashlib
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("data") / "werewolf"
DB_PATH = DATA_DIR / "users.db"
AVATAR_DIR = DATA_DIR / "avatars"

USERNAME_MIN = 2
USERNAME_MAX = 12
QQ_MIN = 5
QQ_MAX = 12
PBKDF2_ITERS = 200_000
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_DISABLED = "disabled"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            create table if not exists users (
                id text primary key,
                qq_uin text unique not null,
                username text not null,
                secret_value text not null,
                password_hash text not null,
                salt text not null,
                iterations integer not null,
                status text not null,
                avatar_filename text,
                created_at integer not null,
                secret_issued_at integer,
                secret_confirmed_at integer,
                last_login_at integer
            )
            """
        )
        _ensure_schema(conn)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("pragma table_info(users)").fetchall()}
    required = {
        "id",
        "qq_uin",
        "username",
        "secret_value",
        "password_hash",
        "salt",
        "iterations",
        "status",
        "avatar_filename",
        "created_at",
        "secret_issued_at",
        "secret_confirmed_at",
        "last_login_at",
    }
    if not required.issubset(columns):
        raise RuntimeError("users 表结构不匹配，请删除 data/werewolf/users.db 后重启。")


def _hash_password(password: str, salt: str, iterations: int) -> str:
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return derived.hex()


def _validate_username(username: str) -> Optional[str]:
    cleaned = username.strip()
    if not cleaned:
        return "empty_username"
    if len(cleaned) < USERNAME_MIN or len(cleaned) > USERNAME_MAX:
        return "username_length"
    for ch in cleaned:
        if ch.isalnum() or "\u4e00" <= ch <= "\u9fff" or ch in {"_", "-"}:
            continue
        return "username_chars"
    return None


def _validate_qq_uin(qq_uin: str) -> Optional[str]:
    cleaned = qq_uin.strip()
    if not cleaned:
        return "empty_qq"
    if not cleaned.isdigit():
        return "qq_chars"
    if len(cleaned) < QQ_MIN or len(cleaned) > QQ_MAX:
        return "qq_length"
    return None


def validate_qq_uin(qq_uin: str) -> Optional[str]:
    return _validate_qq_uin(qq_uin)


def provision_user(qq_uin: str, display_name: Optional[str] = None) -> dict:
    error = _validate_qq_uin(qq_uin)
    if error:
        raise ValueError(error)
    cleaned = qq_uin.strip()
    desired_name = (display_name or "").strip()
    if desired_name:
        if _validate_username(desired_name):
            desired_name = ""
    if not desired_name:
        desired_name = f"玩家{cleaned[-4:]}"

    with _connect() as conn:
        row = conn.execute(
            "select id, username, secret_value, status from users where qq_uin = ?",
            (cleaned,),
        ).fetchone()
        if row:
            user_id, current_name, secret_value, status = row
            if status == STATUS_DISABLED:
                raise ValueError("user_disabled")
            if desired_name and desired_name != current_name:
                conn.execute("update users set username = ? where id = ?", (desired_name, user_id))
                current_name = desired_name
            return {
                "id": user_id,
                "qq_uin": cleaned,
                "username": current_name,
                "status": status,
                "secret": secret_value,
            }

        secret = secrets.token_urlsafe(16)
        salt = secrets.token_hex(8)
        password_hash = _hash_password(secret, salt, PBKDF2_ITERS)
        user_id = uuid.uuid4().hex
        created_at = int(time.time())
        conn.execute(
            "insert into users (id, qq_uin, username, secret_value, password_hash, salt, iterations, "
            "status, avatar_filename, created_at, secret_issued_at) "
            "values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                cleaned,
                desired_name,
                secret,
                password_hash,
                salt,
                PBKDF2_ITERS,
                STATUS_PENDING,
                None,
                created_at,
                created_at,
            ),
        )
        return {
            "id": user_id,
            "qq_uin": cleaned,
            "username": desired_name,
            "status": STATUS_PENDING,
            "secret": secret,
        }


def confirm_user(qq_uin: str) -> dict:
    error = _validate_qq_uin(qq_uin)
    if error:
        raise ValueError(error)
    cleaned = qq_uin.strip()
    now = int(time.time())
    with _connect() as conn:
        row = conn.execute(
            "select id, status, secret_confirmed_at from users where qq_uin = ?",
            (cleaned,),
        ).fetchone()
        if not row:
            raise ValueError("user_not_found")
        user_id, status, confirmed_at = row
        if status == STATUS_DISABLED:
            raise ValueError("user_disabled")
        if status != STATUS_ACTIVE or confirmed_at is None:
            conn.execute(
                "update users set status = ?, secret_confirmed_at = ? where qq_uin = ?",
                (STATUS_ACTIVE, now, cleaned),
            )
        return {"id": user_id, "qq_uin": cleaned, "status": STATUS_ACTIVE}


def authenticate_by_qq(qq_uin: str, secret: str) -> Optional[dict]:
    error = _validate_qq_uin(qq_uin)
    if error:
        raise ValueError(error)
    cleaned = qq_uin.strip()
    if not secret:
        raise ValueError("empty_secret")
    with _connect() as conn:
        row = conn.execute(
            "select id, qq_uin, username, password_hash, salt, iterations, status, avatar_filename "
            "from users where qq_uin = ?",
            (cleaned,),
        ).fetchone()
        if not row:
            return None
        user_id, qq_uin_value, name, password_hash, salt, iterations, status, avatar_filename = row
        if status != STATUS_ACTIVE:
            return None
        if _hash_password(secret, salt, iterations) != password_hash:
            return None
        conn.execute("update users set last_login_at = ? where id = ?", (int(time.time()), user_id))
        return {
            "id": user_id,
            "qq_uin": qq_uin_value,
            "username": name,
            "avatar_filename": avatar_filename,
        }


def get_user_by_id(user_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "select id, qq_uin, username, avatar_filename from users where id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "qq_uin": row[1], "username": row[2], "avatar_filename": row[3]}


def get_user_by_qq(qq_uin: str) -> Optional[dict]:
    cleaned = qq_uin.strip()
    with _connect() as conn:
        row = conn.execute(
            "select id, qq_uin, username, avatar_filename, status from users where qq_uin = ?",
            (cleaned,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "qq_uin": row[1],
        "username": row[2],
        "avatar_filename": row[3],
        "status": row[4],
    }


def update_display_name(user_id: str, display_name: str) -> None:
    error = _validate_username(display_name)
    if error:
        raise ValueError(error)
    with _connect() as conn:
        conn.execute("update users set username = ? where id = ?", (display_name.strip(), user_id))


def update_avatar(user_id: str, filename: str) -> None:
    with _connect() as conn:
        conn.execute("update users set avatar_filename = ? where id = ?", (filename, user_id))


def avatar_url(base_path: str, avatar_filename: Optional[str]) -> Optional[str]:
    if not avatar_filename:
        return None
    return f"{base_path}/avatars/{avatar_filename}"

