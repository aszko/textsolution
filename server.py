from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Autoriser le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # remplace par l'URL de ton frontend en prod si besoin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage temporaire des messages
messages = []

class Message(BaseModel):
    user: str
    text: str

# ------------------ Routes REST ------------------

@app.post("/login")
def login(user: str, password: str):
    return {"status": "ok", "message": f"Connecté en tant que {user}"}

@app.post("/register")
def register(user: str, password: str):
    return {"status": "ok", "message": f"Compte créé pour {user}"}

@app.post("/send")
def send_message(msg: Message):
    messages.append(msg.dict())
    return {"status": "ok"}

@app.get("/messages")
def get_messages():
    return {"messages": messages}

# ------------------ WebSocket ------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_json()
        messages.append(data)
        await ws.send_json(messages)
