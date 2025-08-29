import asyncio
import json
import os
import time
import hashlib
import hmac
import secrets
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

# -------- Fichiers --------
USERS_FILE = "users.json"
MSGS_FILE = "messages.json"

# -------- Utilitaires --------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de {path}: {e}")
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

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
    db["users"].append({
        "username": username,
        "salt": salt,
        "pwd_hash": pwd_hash
    })
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

# -------- Serveur FastAPI --------
app = FastAPI()
clients: List[WebSocket] = []

@app.get("/")
def root():
    return {"status": "ok", "message": "Serveur de chat en ligne"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    username = None
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "auth":
                action = data.get("action")
                u = data.get("username")
                p = data.get("password")
                if not u or not p:
                    await websocket.send_json({"type": "auth", "status": "error", "message": "Pseudo et mot de passe requis."})
                    continue
                if action == "register":
                    ok, msg = register_user(u, p)
                    await websocket.send_json({"type": "auth", "status": "ok" if ok else "error", "message": msg})
                elif action == "login":
                    if verify_user(u, p):
                        username = u
                        await websocket.send_json({"type": "auth", "status": "ok", "message": "Connecté."})
                    else:
                        await websocket.send_json({"type": "auth", "status": "error", "message": "Pseudo ou mot de passe incorrect."})
                else:
                    await websocket.send_json({"type": "auth", "status": "error", "message": "Action inconnue."})
            elif data.get("type") == "msg":
                if not username:
                    await websocket.send_json({"type": "error", "message": "Non authentifié."})
                    continue
                text = (data.get("text") or "").strip()
                if not text:
                    continue
                msg_obj = {"type": "msg", "from": username, "text": text, "ts": int(time.time())}
                append_message(msg_obj)
                # broadcast
                for client in clients[:]:
                    try:
                        await client.send_json(msg_obj)
                    except Exception:
                        clients.remove(client)
            else:
                await websocket.send_json({"type": "error", "message": "Type inconnu."})
    except WebSocketDisconnect:
        clients.remove(websocket)
    except Exception as e:
        print(f"Erreur WebSocket: {e}")
        if websocket in clients:
            clients.remove(websocket)

# -------- Lancement serveur --------
if __name__ == "__main__":
    # Assure que les fichiers existent
    load_json(USERS_FILE, {"users": []})
    load_json(MSGS_FILE, {"messages": []})

    PORT = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
