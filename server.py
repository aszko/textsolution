import json, os, secrets, hashlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# Permet au client local de communiquer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "database"
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
FRIENDS_FILE = os.path.join(DATA_DIR, "friends.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

# ---------------- UTILS ----------------
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def generate_token():
    return secrets.token_hex(32)

# ---------------- MODELS ----------------
class AuthRequest(BaseModel):
    action: str
    username: str
    password: str

class MessageRequest(BaseModel):
    from_user: str
    text: str
    token: str

class FriendRequest(BaseModel):
    username: str
    friend: str
    token: str

# ---------------- AUTH ----------------
@app.post("/auth")
def auth(req: AuthRequest):
    users = load_json(USERS_FILE, {})
    sessions = load_json(SESSIONS_FILE, {})

    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Remplis tous les champs")

    if req.action == "register":
        if req.username in users:
            raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
        users[req.username] = hash_password(req.password)
        save_json(USERS_FILE, users)
        token = generate_token()
        sessions[req.username] = token
        save_json(SESSIONS_FILE, sessions)
        return {"status": "ok", "token": token}

    elif req.action == "login":
        if req.username not in users or users[req.username] != hash_password(req.password):
            raise HTTPException(status_code=400, detail="Login incorrect")
        token = generate_token()
        sessions[req.username] = token
        save_json(SESSIONS_FILE, sessions)
        return {"status": "ok", "token": token}

    else:
        raise HTTPException(status_code=400, detail="Action inconnue")

# ---------------- MESSAGE ----------------
@app.post("/send")
def send_message(req: MessageRequest):
    sessions = load_json(SESSIONS_FILE, {})
    if req.from_user not in sessions or sessions[req.from_user] != req.token:
        raise HTTPException(status_code=401, detail="Token invalide")
    if not req.text:
        raise HTTPException(status_code=400, detail="Message vide")
    messages = load_json(MESSAGES_FILE, [])
    messages.append({"from_user": req.from_user, "text": req.text})
    save_json(MESSAGES_FILE, messages)
    return {"status": "ok"}

@app.get("/messages")
def get_messages(token: Optional[str] = None, username: Optional[str] = None):
    sessions = load_json(SESSIONS_FILE, {})
    if username not in sessions or sessions[username] != token:
        raise HTTPException(status_code=401, detail="Token invalide")
    messages = load_json(MESSAGES_FILE, [])
    return messages

# ---------------- FRIENDS ----------------
@app.get("/friends")
def get_friends(username: str, token: str):
    sessions = load_json(SESSIONS_FILE, {})
    if username not in sessions or sessions[username] != token:
        raise HTTPException(status_code=401, detail="Token invalide")
    friends = load_json(FRIENDS_FILE, {})
    return friends.get(username, [])

@app.post("/friends")
def add_friend(req: FriendRequest):
    sessions = load_json(SESSIONS_FILE, {})
    if req.username not in sessions or sessions[req.username] != req.token:
        raise HTTPException(status_code=401, detail="Token invalide")
    friends = load_json(FRIENDS_FILE, {})
    friends.setdefault(req.username, [])
    if req.friend not in friends[req.username]:
        friends[req.username].append(req.friend)
    save_json(FRIENDS_FILE, friends)
    return {"status": "ok"}

# ---------------- PROFILE ----------------
@app.post("/profile/avatar")
def change_avatar(username: str, token: str, avatar_url: str):
    sessions = load_json(SESSIONS_FILE, {})
    if username not in sessions or sessions[username] != token:
        raise HTTPException(status_code=401, detail="Token invalide")
    users = load_json(USERS_FILE, {})
    if username not in users:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    users[username+"_avatar"] = avatar_url
    save_json(USERS_FILE, users)
    return {"status": "ok"}
