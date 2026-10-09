from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import sqlite3, json, os, time

DB = Path(os.environ.get("APICULTURE_DB", "apiculture_sync.db"))
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
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS states(
        user_id TEXT PRIMARY KEY,
        revision INTEGER NOT NULL,
        state TEXT NOT NULL,
        updated_at INTEGER NOT NULL
    )""")
    c.commit()
    return c

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
    c = db()
    row = c.execute("SELECT revision,state,updated_at FROM states WHERE user_id=?", (user_id,)).fetchone()
    c.close()
    if not row:
        raise HTTPException(status_code=404, detail="Aucune donnée")
    return {"revision": row[0], "state": json.loads(row[1]), "updated_at": row[2]}

@app.put("/api/state/{user_id}")
def put_state(user_id: str, payload: Push, authorization: str | None = Header(default=None)):
    auth(authorization)
    c = db()
    row = c.execute("SELECT revision FROM states WHERE user_id=?", (user_id,)).fetchone()
    current = row[0] if row else 0
    if current != payload.base_revision:
        c.close()
        raise HTTPException(status_code=409, detail="Révision différente")
    new_rev = current + 1
    c.execute(
        "INSERT INTO states(user_id,revision,state,updated_at) VALUES(?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET revision=excluded.revision,state=excluded.state,updated_at=excluded.updated_at",
        (user_id, new_rev, json.dumps(payload.state, ensure_ascii=False), int(time.time()))
    )
    c.commit()
    c.close()
    return {"ok": True, "revision": new_rev}
