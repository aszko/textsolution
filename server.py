import json, os, uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Utils ----------
def load_json(file_path, default):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump(default, f)
    with open(file_path, "r") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ---------- Routes ----------
@app.post("/auth")
async def auth(request: Request):
    data = await request.json()
    action = data.get("action")
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Remplis tous les champs")

    users = load_json(USERS_FILE, {})

    if action == "register":
        if username in users:
            raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
        token = str(uuid.uuid4())
        users[username] = {"password": password, "token": token}
        save_json(USERS_FILE, users)
        return {"status":"ok","token":token}

    elif action == "login":
        if username not in users or users[username]["password"] != password:
            raise HTTPException(status_code=400, detail="Login incorrect")
        token = str(uuid.uuid4())  # nouveau token à chaque login
        users[username]["token"] = token
        save_json(USERS_FILE, users)
        return {"status":"ok","token":token}

    else:
        raise HTTPException(status_code=400, detail="Action inconnue")

@app.get("/validate")
async def validate(token: str):
    users = load_json(USERS_FILE, {})
    for u,v in users.items():
        if v.get("token") == token:
            return {"status":"ok","username":u}
    raise HTTPException(status_code=401, detail="Token invalide")

@app.post("/send")
async def send(request: Request, token: str):
    data = await request.json()
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Message vide")

    users = load_json(USERS_FILE, {})
    sender = None
    for u,v in users.items():
        if v.get("token") == token:
            sender = u
            break
    if not sender:
        raise HTTPException(status_code=401, detail="Token invalide")

    messages = load_json(MESSAGES_FILE, [])
    messages.append({"from_user": sender, "text": text})
    save_json(MESSAGES_FILE, messages)
    return {"status":"ok"}

@app.get("/messages")
async def get_messages(token: str):
    users = load_json(USERS_FILE, {})
    valid = any(v.get("token") == token for v in users.values())
    if not valid:
        raise HTTPException(status_code=401, detail="Token invalide")
    messages = load_json(MESSAGES_FILE, [])
    return messages

# ---------- Main ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
