import json
import os
from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)

USERS_FILE = "users.json"

lock = Lock()

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

def load_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

# ---------------- AUTH ----------------
@app.route("/auth", methods=["POST"])
def auth():
    data = request.get_json()
    action = data.get("action")
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"status": "error", "message": "Remplis tous les champs"}), 400

    with lock:
        users = load_users()

        if action == "register":
            if username in users:
                return jsonify({"status": "error", "message": "Utilisateur déjà existant"}), 400
            users[username] = password
            save_users(users)
            return jsonify({"status": "ok"})
        
        elif action == "login":
            if username not in users or users[username] != password:
                return jsonify({"status": "error", "message": "Login incorrect"}), 400
            return jsonify({"status": "ok"})
        
        else:
            return jsonify({"status": "error", "message": "Action inconnue"}), 400

# ---------------- MESSAGES EN MEMOIRE ----------------
messages = []

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    sender = data.get("from")
    text = data.get("text")

    if not sender or not text:
        return jsonify({"status": "error", "message": "Données invalides"}), 400

    messages.append({"from": sender, "text": text})
    return jsonify({"status": "ok"})

@app.route("/messages", methods=["GET"])
def get_messages():
    return jsonify(messages)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
