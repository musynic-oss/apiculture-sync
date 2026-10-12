from fastapi import FastAPI, HTTPException, Header, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
import os, json, time, hashlib, hmac
import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
SYNC_TOKEN = os.environ.get("APICULTURE_SYNC_TOKEN", "change-me")

app = FastAPI(title="Apiculture Sync")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","PUT","POST","OPTIONS"],
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

SESSION_COOKIE = "apiculture_session"
SESSION_VALUE = hmac.new(
    SYNC_TOKEN.encode("utf-8"),
    b"apiculture-session-v1",
    hashlib.sha256
).hexdigest()

def bearer_ok(authorization: str | None):
    return bool(authorization) and hmac.compare_digest(authorization, f"Bearer {SYNC_TOKEN}")

def session_ok(apiculture_session: str | None):
    return bool(apiculture_session) and hmac.compare_digest(apiculture_session, SESSION_VALUE)

def auth(authorization: str | None, apiculture_session: str | None):
    if not (bearer_ok(authorization) or session_ok(apiculture_session)):
        raise HTTPException(status_code=401, detail="Jeton invalide")

class Push(BaseModel):
    base_revision: int = 0
    state: dict

@app.post("/api/session")
def create_session(response: Response, authorization: str | None = Header(default=None)):
    if not bearer_ok(authorization):
        raise HTTPException(status_code=401, detail="Jeton invalide")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=SESSION_VALUE,
        max_age=31536000,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/"
    )
    return {"ok": True}

@app.get("/api/health")
def health(
    authorization: str | None = Header(default=None),
    apiculture_session: str | None = Cookie(default=None)
):
    auth(authorization, apiculture_session)
    return {"ok": True}

@app.get("/api/state/{user_id}")
def get_state(
    user_id: str,
    authorization: str | None = Header(default=None),
    apiculture_session: str | None = Cookie(default=None)
):
    auth(authorization, apiculture_session)
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
def put_state(
    user_id: str,
    payload: Push,
    authorization: str | None = Header(default=None),
    apiculture_session: str | None = Cookie(default=None)
):
    auth(authorization, apiculture_session)
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

# Application web installable (PWA). Les routes /api/... définies ci-dessus restent prioritaires.
WEB_DIR = Path(__file__).parent / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
