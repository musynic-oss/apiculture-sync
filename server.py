from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, json, time
import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
SYNC_TOKEN = os.environ.get("APICULTURE_SYNC_TOKEN", "change-me")

app = FastAPI(title="Apiculture Sync")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","PUT","OPTIONS"],
    allow_headers=["*"],
)

def db():
    conn = psycopg.connect(DATABASE_URL)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS states(
            user_id TEXT PRIMARY KEY,
            revision INTEGER NOT NULL,
            state JSONB NOT NULL,
            updated_at BIGINT NOT NULL
        )
    """)
    conn.commit()
    return conn

def auth(authorization: str | None):
    if not authorization or authorization != f"Bearer {SYNC_TOKEN}":
        raise HTTPException(status_code=401, detail="Jeton invalide")

class Push(BaseModel):
    base_revision: int = 0
    state: dict

@app.get("/api/health")
def health(authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"ok": True}

@app.get("/api/state/{user_id}")
def get_state(user_id: str, authorization: str | None = Header(default=None)):
    auth(authorization)
    conn = db()
    row = conn.execute(
        "SELECT revision, state, updated_at FROM states WHERE user_id=%s",
        (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Aucune donnée")
    return {"revision": row[0], "state": row[1], "updated_at": row[2]}

@app.put("/api/state/{user_id}")
def put_state(user_id: str, payload: Push, authorization: str | None = Header(default=None)):
    auth(authorization)
    conn = db()
    row = conn.execute(
        "SELECT revision FROM states WHERE user_id=%s",
        (user_id,)
    ).fetchone()
    current = row[0] if row else 0
    if current != payload.base_revision:
        conn.close()
        raise HTTPException(status_code=409, detail="Révision différente")
    new_rev = current + 1
    conn.execute(
        """
        INSERT INTO states(user_id, revision, state, updated_at)
        VALUES(%s,%s,%s::jsonb,%s)
        ON CONFLICT(user_id) DO UPDATE SET
            revision=EXCLUDED.revision,
            state=EXCLUDED.state,
            updated_at=EXCLUDED.updated_at
        """,
        (user_id, new_rev, json.dumps(payload.state, ensure_ascii=False), int(time.time()))
    )
    conn.commit()
    conn.close()
    return {"ok": True, "revision": new_rev}
