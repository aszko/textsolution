import json, os, uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# ------------------ Fichiers ------------------
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"
SESSIONS_FILE = "sessions.json"
FRIENDS_FILE = "friends.json"

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ------------------ Models ------------------
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

# ------------------ Utils ------------------
def load_json(file_path, default={}):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default, f)
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ------------------ Auth ------------------
@app.post("/auth")
def auth(req: AuthRequest):
    users = load_json(USERS_FILE, {})
    sessions = load_json(SESSIONS_FILE, {})

    if req.action == "register":
        if req.username in users:
            raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
        users[req.username] = req.password
        token = str(uuid.uuid4())
        sessions[req.username] = token
        save_json(USERS_FILE, users)
        save_json(SESSIONS_FILE, sessions)
        return {"status": "ok", "token": token}

    elif req.action == "login":
        if req.username not in users or users[req.username] != req.password:
            raise HTTPException(status_code=400, detail="Login incorrect")
        token = sessions.get(req.username, str(uuid.uuid4()))
        sessions[req.username] = token
        save_json(SESSIONS_FILE, sessions)
        return {"status": "ok", "token": token}

    else:
        raise HTTPException(status_code=400, detail="Action inconnue")

# ------------------ Messages ------------------
@app.post("/send")
def send(req: MessageRequest):
    users = load_json(USERS_FILE, {})
    sessions = load_json(SESSIONS_FILE, {})
    messages = load_json(MESSAGES_FILE, [])

    if req.from_user not in sessions or sessions[req.from_user] != req.token:
        raise HTTPException(status_code=403, detail="Token invalide")

    messages.append({"from_user": req.from_user, "text": req.text})
    save_json(MESSAGES_FILE, messages)
    return {"status": "ok"}

@app.get("/messages")
def get_messages():
    return load_json(MESSAGES_FILE, [])

# ------------------ Friends ------------------
@app.post("/add_friend")
def add_friend(req: FriendRequest):
    users = load_json(USERS_FILE, {})
    sessions = load_json(SESSIONS_FILE, {})
    friends = load_json(FRIENDS_FILE, {})

    if req.username not in sessions or sessions[req.username] != req.token:
        raise HTTPException(status_code=403, detail="Token invalide")
    if req.friend not in users:
        raise HTTPException(status_code=400, detail="Ami inexistant")

    friends.setdefault(req.username, [])
    if req.friend not in friends[req.username]:
        friends[req.username].append(req.friend)
        save_json(FRIENDS_FILE, friends)
    return {"status": "ok"}

@app.post("/remove_friend")
def remove_friend(req: FriendRequest):
    sessions = load_json(SESSIONS_FILE, {})
    friends = load_json(FRIENDS_FILE, {})

    if req.username not in sessions or sessions[req.username] != req.token:
        raise HTTPException(status_code=403, detail="Token invalide")

    friends.setdefault(req.username, [])
    if req.friend in friends[req.username]:
        friends[req.username].remove(req.friend)
        save_json(FRIENDS_FILE, friends)
    return {"status": "ok"}

@app.get("/friends/{username}")
def list_friends(username: str, token: str):
    sessions = load_json(SESSIONS_FILE, {})
    friends = load_json(FRIENDS_FILE, {})

    if username not in sessions or sessions[username] != token:
        raise HTTPException(status_code=403, detail="Token invalide")
    return friends.get(username, [])

# ------------------ Lancement ------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
