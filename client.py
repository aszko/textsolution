import sys
import json
import threading
import websocket
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

ws_url = "ws://localhost:5000/"  # Utilisation de ws pour WebSocket

class WSClient(threading.Thread):
    def __init__(self, url, on_msg, on_auth):
        super().__init__(daemon=True)
        self.url = url
        self.on_msg = on_msg
        self.on_auth = on_auth
        self.ws = None

    def run(self):
        self.connect()

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=lambda ws, msg: self.handle_message(msg),
            on_close=self.on_close,
            on_error=self.on_error
        )
        self.ws.run_forever()

    def handle_message(self, msg):
        data = json.loads(msg)
        if data["type"] == "msg":
            self.on_msg(data)
        elif data["type"] == "auth":
            self.on_auth(data)

    def on_close(self, ws, close_status_code):
        print("Connexion fermée, tentant de se reconnecter...")
        self.connect()

    def on_error(self, ws, error):
        print(f"Erreur : {error}")

    def send(self, obj):
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps(obj))
        else:
            print("Erreur: WebSocket non connecté.")

# ---------- UI ----------
class LoginPage(QWidget):
    def __init__(self, on_login, on_register):
        super().__init__()
        layout = QVBoxLayout(self)
        self.user = QLineEdit()
        self.user.setPlaceholderText("Pseudo")
        self.passw = QLineEdit()
        self.passw.setPlaceholderText("Mot de passe")
        self.passw.setEchoMode(QLineEdit.Password)

        btn_login = QPushButton("Se connecter")
        btn_login.clicked.connect(lambda: on_login(self.user.text(), self.passw.text()))
        btn_register = QPushButton("Créer un compte")
        btn_register.clicked.connect(lambda: on_register(self.user.text(), self.passw.text()))

        layout.addWidget(QLabel("Connexion"))
        layout.addWidget(self.user)
        layout.addWidget(self.passw)
        layout.addWidget(btn_login)
        layout.addWidget(btn_register)

# Continuer avec le reste de votre interface utilisateur...

class ChatPage(QWidget):
    def __init__(self, on_send):
        super().__init__()
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Écris ton message…")
        send_btn = QPushButton("➤")
        send_btn.clicked.connect(lambda: (on_send(self.input.text()), self.input.clear()))

        hl = QHBoxLayout()
        hl.addWidget(self.input)
        hl.addWidget(send_btn)

        layout.addWidget(self.list)
        layout.addLayout(hl)

    def add_msg(self, sender, text, me=False):
        item = QListWidgetItem(f"{sender}: {text}")
        item.setTextAlignment(Qt.AlignRight if me else Qt.AlignLeft)
        self.list.addItem(item)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Privé")
        self.resize(400, 600)
        self.stack = QStackedWidget()
        self.login = LoginPage(self.do_login, self.do_register)
        self.chat = ChatPage(self.do_send)
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.chat)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        self.client = WSClient(ws_url, self.on_msg, self.on_auth)
        self.client.start()
        self.username = None

    def do_login(self, user, pw):
        self.username = user
        self.client.send({"type": "auth", "action": "login", "username": user, "password": pw})

    def do_register(self, user, pw):
        self.client.send({"type": "auth", "action": "register", "username": user, "password": pw})

    def do_send(self, txt):
        self.client.send({"type": "msg", "text": txt})
        self.chat.add_msg(self.username, txt, me=True)

    def on_msg(self, obj):
        sender, text = obj["from"], obj["text"]
        me = (sender == self.username)
        self.chat.add_msg(sender, text, me)

    def on_auth(self, obj):
        if obj["status"] == "ok":
            self.stack.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Erreur", obj["message"])

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    w = App()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()