import os, json, uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from threading import Lock

app = FastAPI()

# Fichiers
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"
SESSIONS_FILE = "sessions.json"

lock = Lock()

# ---------------- UTILS ----------------
def load_json(file_path, default):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default, f)
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- MODELS ----------------
class AuthRequest(BaseModel):
    action: str
    username: str
    password: str

class MessageRequest(BaseModel):
    token: str
    text: str

# ---------------- AUTH ----------------
@app.post("/auth")
def auth(req: AuthRequest):
    with lock:
        users = load_json(USERS_FILE, {})
        sessions = load_json(SESSIONS_FILE, {})

        if req.action == "register":
            if req.username in users:
                raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
            users[req.username] = req.password
            save_json(USERS_FILE, users)

        elif req.action == "login":
            if req.username not in users or users[req.username] != req.password:
                raise HTTPException(status_code=400, detail="Identifiants invalides")

        # Création token
        token = str(uuid.uuid4())
        sessions[token] = req.username
        save_json(SESSIONS_FILE, sessions)

        return {"status": "ok", "token": token}

# ---------------- SEND MESSAGE ----------------
@app.post("/send")
def send(req: MessageRequest):
    with lock:
        sessions = load_json(SESSIONS_FILE, {})
        if req.token not in sessions:
            raise HTTPException(status_code=401, detail="Session invalide")

        username = sessions[req.token]
        messages = load_json(MESSAGES_FILE, [])
        msg_id = len(messages) + 1
        messages.append({"id": msg_id, "from_user": username, "text": req.text})
        save_json(MESSAGES_FILE, messages)

        return {"status": "ok"}

# ---------------- GET MESSAGES ----------------
@app.get("/messages")
def get_messages():
    with lock:
        return load_json(MESSAGES_FILE, [])

# ---------------- MAIN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
