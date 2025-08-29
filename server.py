import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from threading import Lock

# ---------------- CONFIG ----------------
USERS_FILE = "users.json"
lock = Lock()
messages = []  # Messages stockés en mémoire

# ---------------- INIT APP ----------------
app = FastAPI(title="ChatSolution API")

# CORS pour le client desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- UTILS ----------------
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

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
        users = load_users()
        if req.action == "register":
            if req.username in users:
                raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
            users[req.username] = req.password
            save_users(users)
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
    messages.append({"from_user": req.from_user, "text": req.text})
    return {"status": "ok"}

@app.get("/messages")
def get_messages():
    return messages

@app.get("/")
def root():
    return {"message": "ChatSolution API en ligne"}

# ---------------- MAIN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=5000, log_level="info")
