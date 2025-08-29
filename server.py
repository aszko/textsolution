import asyncio
import json
import os
import time
import hashlib
import hmac
import secrets
import websockets

# -------- Fichiers --------
USERS_FILE = "users.json"
MSGS_FILE = "messages.json"
clients = set()

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
        print(f"Erreur lors du chargement de la json: {e}")
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
    return hmac.new(bytes.fromhex(salt), password.encode("utf-8"),
                    hashlib.sha256).hexdigest()

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
            return hmac.compare_digest(u["pwd_hash"],
                                       hash_password(password, u["salt"]))
    return False

def append_message(msg_obj):
    db = load_json(MSGS_FILE, {"messages": []})
    db["messages"].append(msg_obj)
    save_json(MSGS_FILE, db)

# -------- WebSocket handler --------
async def handler(websocket, path):
    clients.add(websocket)
    username = None
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "auth":
                if data["action"] == "register":
                    ok, msg = register_user(data["username"], data["password"])
                    await websocket.send(
                        json.dumps({
                            "type": "auth",
                            "status": "ok" if ok else "error",
                            "message": msg
                        }))
                elif data["action"] == "login":
                    if verify_user(data["username"], data["password"]):
                        username = data["username"]
                        await websocket.send(
                            json.dumps({
                                "type": "auth",
                                "status": "ok",
                                "message": "Connecté."
                            }))
                    else:
                        await websocket.send(
                            json.dumps({
                                "type": "auth",
                                "status": "error",
                                "message": "Pseudo ou mot de passe incorrect."
                            }))
            elif data["type"] == "msg" and username:
                msg_obj = {
                    "type": "msg",
                    "from": username,
                    "text": data["text"],
                    "ts": int(time.time())
                }
                append_message(msg_obj)
                for client in list(clients):
                    try:
                        await client.send(json.dumps(msg_obj))
                    except Exception as e:
                        print(f"Erreur lors de l'envoi au client: {e}")
    except Exception as e:
        print(f"Erreur dans le gestionnaire WebSocket: {e}")
    finally:
        clients.remove(websocket)
        
@app.route("/")
def home():
    return "✅ Serveur de chat en ligne (WebSocket disponible sur /ws)"

async def main():
    PORT = 5000  # Utilisez le port 5000 pour le développement
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"WebSocket en écoute sur ws://0.0.0.0:{PORT}")
        await asyncio.Future()  # Exécute ce futur indéfiniment

if __name__ == "__main__":
    load_json(USERS_FILE, {"users": []})
    load_json(MSGS_FILE, {"messages": []})
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    asyncio.run(main())
