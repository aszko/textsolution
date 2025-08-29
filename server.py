import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from threading import Lock

# ---------------- CONFIG ----------------
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"
lock = Lock()

# ---------------- INIT APP ----------------
app = FastAPI(title="ChatSolution API")

# Autoriser le CORS pour ton client desktop ou autre domaine si nécessaire
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour desktop, on peut laisser *
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- UTILS ----------------
def load_json(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({} if "users" in file_path else [], f)
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
    from_user: str
    text: str

# ---------------- ROUTES ----------------
@app.post("/auth")
def auth(req: AuthRequest):
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Remplis tous les champs")

    with lock:
        users = load_json(USERS_FILE)
        if req.action == "register":
            if req.username in users:
                raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
            users[req.username] = req.password
            save_json(USERS_FILE, users)
            return {"status": "ok"}
        elif req.action == "login":
            if req.username not in users or users[req.username] != req.password:
                raise HTTPException(status_code=400, detail="Login incorrect")
            return {"status": "ok"}
        else:
            raise HTTPException(status_code=400, detail="Action inconnue")

@app.post("/send")
def send(req: MessageRequest):
    if not req.from_user or not req.text:
        raise HTTPException(status_code=400, detail="Données invalides")
    with lock:
        messages = load_json(MESSAGES_FILE)
        messages.append({"from": req.from_user, "text": req.text})
        save_json(MESSAGES_FILE, messages)
    return {"status": "ok"}

@app.get("/messages")
def get_messages():
    with lock:
        messages = load_json(MESSAGES_FILE)
    return messages

# ---------------- MAIN ----------------
if __name__ == "__main__":
    import uvicorn
    # Render gère HTTPS automatiquement
    uvicorn.run("server:app", host="0.0.0.0", port=5000, log_level="info")
