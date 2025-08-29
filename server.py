from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import json, uuid, os

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_FILE = os.path.join(BASE_DIR, "users.json")
SESSIONS_FILE = os.path.join(BASE_DIR, "sessions.json")
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")

# Autoriser le client desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_json(path):
    if not os.path.exists(path):
        return {} if "users" in path or "sessions" in path else []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ---------------- AUTH ----------------
@app.post("/auth")
def auth(action: str, username: str, password: str):
    users = load_json(USERS_FILE)
    sessions = load_json(SESSIONS_FILE)

    if action == "register":
        if username in users:
            raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
        users[username] = password
        save_json(USERS_FILE, users)

    elif action == "login":
        if username not in users or users[username] != password:
            raise HTTPException(status_code=400, detail="Login incorrect")
    else:
        raise HTTPException(status_code=400, detail="Action inconnue")

    # Génération du token de session
    token = str(uuid.uuid4())
    sessions[token] = username
    save_json(SESSIONS_FILE, sessions)
    return {"status": "ok", "token": token}

# ---------------- SEND MESSAGE ----------------
@app.post("/send")
def send(text: str, token: str = Header(...)):
    sessions = load_json(SESSIONS_FILE)
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Session invalide")
    username = sessions[token]

    messages = load_json(MESSAGES_FILE)
    messages.append({"from_user": username, "text": text})
    save_json(MESSAGES_FILE, messages)
    return {"status": "ok"}

# ---------------- GET MESSAGES ----------------
@app.get("/messages")
def get_messages(token: str = Header(...)):
    sessions = load_json(SESSIONS_FILE)
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Session invalide")
    messages = load_json(MESSAGES_FILE)
    return messages
