import sqlite3
import json
import time
from pathlib import Path

DB_PATH = Path("backend/database.db")

DDL_CARDS = """
CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    detected_image_url TEXT NOT NULL,
    status TEXT NOT NULL,               -- GOOD / FAIL
    scores_json TEXT NOT NULL,          -- {"normal print":0.0,"print header":0.0,"spaghetti":0.0}
    updated_at TEXT NOT NULL,           -- ISO8601
    model TEXT NOT NULL                 -- e.g. best.pt
);
"""

DDL_APIKEYS = """
CREATE TABLE IF NOT EXISTS apikeys (
    api_key TEXT PRIMARY KEY,
    card_id TEXT NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    expires_at REAL NOT NULL,           -- epoch seconds
    used INTEGER NOT NULL DEFAULT 0     -- optional (0/1) if you want one-time
);
"""

DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_keys_card ON apikeys(card_id);
CREATE INDEX IF NOT EXISTS idx_keys_exp ON apikeys(expires_at);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(DDL_CARDS)
        cur.execute(DDL_APIKEYS)
        for stmt in DDL_INDEXES.strip().splitlines():
            if stmt.strip():
                cur.execute(stmt)
        conn.commit()

# --------- Cards CRUD ---------
def upsert_card(card: dict):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO cards(card_id, detected_image_url, status, scores_json, updated_at, model)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
              detected_image_url=excluded.detected_image_url,
              status=excluded.status,
              scores_json=excluded.scores_json,
              updated_at=excluded.updated_at,
              model=excluded.model
        """, (
            card["card_id"], card["detected_image_url"], card["status"],
            json.dumps(card.get("scores", {})), card["updated_at"], card["model"]
        ))
        conn.commit()

def get_card(card_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards WHERE card_id = ?", (card_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "card_id": row["card_id"],
            "detected_image_url": row["detected_image_url"],
            "status": row["status"],
            "scores": json.loads(row["scores_json"]),
            "updated_at": row["updated_at"],
            "model": row["model"],
        }

def list_cards(limit: int = 50, cursor: str | None = None) -> list[dict]:
    # cursor ไม่บังคับใช้ใน MVP (สามารถต่อยอดเป็น keyset pagination ได้)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards ORDER BY updated_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        items = []
        for r in rows:
            items.append({
                "card_id": r["card_id"],
                "detected_image_url": r["detected_image_url"],
                "status": r["status"],
                "scores": json.loads(r["scores_json"]),
                "updated_at": r["updated_at"],
                "model": r["model"],
            })
        return items

# --------- API Keys ---------
def create_apikey(card_id: str, ttl_seconds: int) -> dict:
    api_key = __import__("uuid").uuid4().hex
    expires_at = time.time() + ttl_seconds
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO apikeys(api_key, card_id, expires_at, used) VALUES (?, ?, ?, 0)",
                    (api_key, card_id, expires_at))
        conn.commit()
    return {"api_key": api_key, "card_id": card_id, "expires_at": expires_at}

def verify_apikey(api_key: str, card_id: str) -> bool:
    now = time.time()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT api_key, card_id, expires_at, used FROM apikeys WHERE api_key = ?", (api_key,))
        row = cur.fetchone()
        if not row:
            return False
        if row["card_id"] != card_id:
            return False
        if row["expires_at"] < now:
            return False
        # ถ้าจะให้ one-time ใช้งานเดียว ให้เช็ค used==0 แล้ว mark used=1
        return True

def mark_apikey_used(api_key: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE apikeys SET used = 1 WHERE api_key = ?", (api_key,))
        conn.commit()

