import sys
import requests
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

SERVER_URL = "https://everlast-solution.onrender.com"

# ---------------- Chat Page ----------------
class ChatPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet(
            "QListWidget{background-color: #121212; border: none;}"
        )
        self.layout.addWidget(self.chat_list)
        self.setLayout(self.layout)

    def add_msg(self, sender, text, me=False):
        widget = QWidget()
        v_layout = QVBoxLayout()
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 10))
        label.setStyleSheet(
            f"padding:8px; border-radius:10px; color: white; background-color: {'#1E88E5' if me else '#333333'}"
        )
        v_layout.addWidget(label, alignment=Qt.AlignRight if me else Qt.AlignLeft)
        widget.setLayout(v_layout)

        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, widget)
        self.chat_list.scrollToBottom()

# ---------------- Login Page ----------------
class LoginPage(QWidget):
    def __init__(self, on_login, on_register):
        super().__init__()
        layout = QVBoxLayout(self)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Pseudo")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Mot de passe")
        self.pass_input.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Se connecter")
        login_btn.clicked.connect(lambda: on_login(self.user_input.text(), self.pass_input.text()))
        register_btn = QPushButton("CrÃ©er un compte")
        register_btn.clicked.connect(lambda: on_register(self.user_input.text(), self.pass_input.text()))

        layout.addWidget(QLabel("Connexion"))
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        self.setLayout(layout)

# ---------------- Main App ----------------
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat PrivÃ©")
        self.resize(400, 600)
        self.username = None

        self.stack = QStackedWidget()
        self.login_page = LoginPage(self.do_login, self.do_register)
        self.chat_page = ChatPage()
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.chat_page)

        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Ã‰cris ton messageâ€¦")
        self.send_btn = QPushButton("âž¤")
        self.send_btn.clicked.connect(self.send_msg)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        layout.addWidget(self.msg_input)
        layout.addWidget(self.send_btn)

        # Thread pour rÃ©cupÃ©rer les messages
        self.running = True
        threading.Thread(target=self.fetch_messages_loop, daemon=True).start()

    # ---------------- Actions ----------------
    def do_register(self, user, pw):
        if not user or not pw:
            QMessageBox.warning(self, "Erreur", "Pseudo et mot de passe requis")
            return
        try:
            resp = requests.post(
                f"{SERVER_URL}/register",
                json={"user": user, "password": pw}
            ).json()
            msg = resp.get("message", str(resp))
            QMessageBox.information(self, "Info", msg)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur serveur: {e}")

    def do_login(self, user, pw):
        if not user or not pw:
            QMessageBox.warning(self, "Erreur", "Pseudo et mot de passe requis")
            return
        try:
            resp = requests.post(
                f"{SERVER_URL}/login",
                json={"user": user, "password": pw}
            ).json()
            if resp.get("status") == "ok":
                self.username = user
                self.stack.setCurrentIndex(1)  # Passer au chat
                QMessageBox.information(self, "Info", resp.get("message", "ConnectÃ©"))
            else:
                QMessageBox.warning(self, "Erreur", resp.get("message", "Erreur"))
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur serveur: {e}")

    def send_msg(self):
        if not self.username:
            QMessageBox.warning(self, "Erreur", "Vous devez Ãªtre connectÃ©")
            return
        text = self.msg_input.text().strip()
        if not text:
            return
        try:
            requests.post(
                f"{SERVER_URL}/send",
                json={"user": self.username, "text": text}
            )
            self.chat_page.add_msg(self.username, text, me=True)
            self.msg_input.clear()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'envoyer le message: {e}")

    # ---------------- RÃ©cupÃ©ration messages ----------------
    def fetch_messages_loop(self):
        last_msgs = []
        while self.running:
            try:
                resp = requests.get(f"{SERVER_URL}/messages").json()
                messages = resp.get("messages", [])
                if messages != last_msgs:
                    self.chat_page.chat_list.clear()
                    for msg in messages:
                        self.chat_page.add_msg(
                            msg["from"], msg["text"], me=(msg["from"] == self.username)
                        )
                    last_msgs = messages
            except:
                pass
            time.sleep(1)

# ---------------- Main ----------------
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    w = App()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
