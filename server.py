import os
import json
import time
import hashlib
import hmac
import secrets
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

USERS_FILE = "users.json"
MSGS_FILE = "messages.json"

# ---------------- helpers fichiers ----------------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

# ---------------- users/messages ----------------
def get_users():
    return load_json(USERS_FILE, {"users": []})

def put_users(db):
    save_json(USERS_FILE, db)

def username_exists(db, username):
    return any(u["username"].lower() == username.lower() for u in db["users"])

def make_salt():
    return secrets.token_hex(16)

def hash_password(password, salt):
    return hmac.new(bytes.fromhex(salt), password.encode("utf-8"), hashlib.sha256).hexdigest()

def register_user(username, password):
    db = get_users()
    if username_exists(db, username):
        return False, "Pseudo déjà pris."
    salt = make_salt()
    pwd_hash = hash_password(password, salt)
    db["users"].append({"username": username, "salt": salt, "pwd_hash": pwd_hash, "created_at": int(time.time())})
    put_users(db)
    return True, "Compte créé."

def verify_user(username, password):
    db = get_users()
    for u in db["users"]:
        if u["username"].lower() == username.lower():
            return hmac.compare_digest(u["pwd_hash"], hash_password(password, u["salt"]))
    return False

def append_message(msg_obj):
    db = load_json(MSGS_FILE, {"messages": []})
    db["messages"].append(msg_obj)
    save_json(MSGS_FILE, db)

# ---------------- FastAPI ----------------
app = FastAPI()

# Autoriser CORS pour que le client puisse envoyer des requêtes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # mettre ton client spécifique si besoin
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Serveur de chat en ligne"}

@app.post("/register")
def http_register(user: str, password: str):
    ok, msg = register_user(user, password)
    return {"status": "ok" if ok else "error", "message": msg}

@app.post("/login")
def http_login(user: str, password: str):
    if verify_user(user, password):
        return {"status": "ok", "message": "Connecté"}
    else:
        return {"status": "error", "message": "Pseudo ou mot de passe incorrect"}

@app.post("/send")
def http_send(user: str, text: str):
    msg_obj = {"type": "msg", "from": user, "text": text, "ts": int(time.time())}
    append_message(msg_obj)
    return {"status": "ok"}

@app.get("/messages")
def http_messages():
    db = load_json(MSGS_FILE, {"messages": []})
    return db

# ---------------- Run ----------------
if __name__ == "__main__":
    # Assure que les fichiers existent
    load_json(USERS_FILE, {"users": []})
    load_json(MSGS_FILE, {"messages": []})

    PORT = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
