from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# --------------------
# Config
# --------------------
ADMIN_CODE = os.getenv("ADMIN_CODE")  # set this in Render / local env

# --------------------
# In-memory user store
# --------------------
users = {}

# --------------------
# Middleware
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for now
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Helpers
# --------------------
def require_admin(request: Request):
    if not ADMIN_CODE:
        # Dev mode: admin protection disabled
        return

    code = request.headers.get("x-admin-code")
    if code != ADMIN_CODE:
        raise HTTPException(status_code=403, detail="Forbidden")

def public_user(user):
    return {
        "id": user["id"],
        "locale": user.get("locale", "US"),
        "daysLived": user.get("daysLived"),
        "weekday": user.get("weekday"),
        "lastUpdated": user.get("lastUpdated"),
    }

# --------------------
# Routes
# --------------------

@app.get("/")
def health():
    return {
        "status": "ok",
        "message": "Double Date API (Python scaffold)"
    }

# Serve admin page
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    with open("admin.html", "r", encoding="utf-8") as f:
        return f.read()

# -------- Admin API --------

@app.post("/create")
async def create_user(request: Request):
    require_admin(request)
    data = await request.json()

    user_id = data.get("id")
    openai_key = data.get("openaiKey")

    if not user_id or not openai_key:
        raise HTTPException(status_code=400, detail="id + openaiKey required")

    if user_id in users:
        raise HTTPException(status_code=400, detail="User already exists")

    users[user_id] = {
        "id": user_id,
        "openaiKey": openai_key,
        "locale": "US",
        "daysLived": None,
        "weekday": None,
        "lastUpdated": None,
    }

    return public_user(users[user_id])

@app.get("/users")
def list_users(request: Request):
    require_admin(request)
    return [public_user(u) for u in users.values()]

@app.delete("/{user_id}/delete")
def delete_user(user_id: str, request: Request):
    require_admin(request)

    if user_id not in users:
        raise HTTPException(status_code=404, detail="Not found")

    del users[user_id]
    return {"ok": True}

@app.patch("/{user_id}/admin-update")
async def admin_update(user_id: str, request: Request):
    require_admin(request)

    if user_id not in users:
        raise HTTPException(status_code=404, detail="Not found")

    data = await request.json()
    if "openaiKey" in data:
        users[user_id]["openaiKey"] = data["openaiKey"]
    if data.get("locale") in ("US", "INTL"):
        users[user_id]["locale"] = data["locale"]

    return public_user(users[user_id])

# -------- User-facing (stub) --------

@app.get("/{user_id}/stats")
def user_stats(user_id: str):
    user = users.get(user_id)
    if not user:
        return {"daysLived": "0", "weekday": ""}

    return {
        "daysLived": user.get("daysLived") or "0",
        "weekday": user.get("weekday") or ""
    }
