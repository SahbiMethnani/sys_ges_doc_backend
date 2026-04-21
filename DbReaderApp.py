import sys
import threading
import time
import subprocess
import socket
import os

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                              QWidget, QPushButton, QHBoxLayout, QLabel, QMessageBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, pyqtSignal, QObject
from PyQt6.QtGui import QFont

STREAMLIT_SCRIPT = "LanceDbReader.py"


def find_free_port(start=8501, end=8600) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Aucun port libre trouvé entre 8501 et 8600.")


def run_streamlit(port: int):
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", STREAMLIT_SCRIPT,
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.runOnSave", "false",
        "--server.fileWatcherType", "none",
        "--browser.gatherUsageStats", "false",
        "--logger.level", "error",
    ])


class StreamlitSignals(QObject):
    ready = pyqtSignal(int)
    error = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📂 LanceDB Reader")
        self.setMinimumSize(1280, 800)

        # Port libre
        try:
            self.port = find_free_port()
        except RuntimeError as e:
            QMessageBox.critical(None, "Erreur", str(e))
            sys.exit(1)

        # Signaux
        self.signals = StreamlitSignals()
        self.signals.ready.connect(self.on_streamlit_ready)
        self.signals.error.connect(self.on_streamlit_error)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barre du haut
        toolbar = QWidget()
        toolbar.setFixedHeight(45)
        toolbar.setStyleSheet("background-color: #1e1e2e;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 0, 12, 0)

        title = QLabel("📂 LanceDB Reader")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))  # ✅ PyQt6
        title.setStyleSheet("color: white;")

        self.status_label = QLabel(f"⏳ Démarrage sur le port {self.port}...")
        self.status_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")

        btn_reload = QPushButton("🔄 Recharger")
        btn_reload.setFixedWidth(110)
        btn_reload.setStyleSheet("""
            QPushButton {
                background: #3b3b5c; color: white;
                border: none; border-radius: 6px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background: #5555aa; }
        """)
        btn_reload.clicked.connect(self.reload_view)

        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.status_label)
        toolbar_layout.addSpacing(12)
        toolbar_layout.addWidget(btn_reload)

        # Vue web
        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)    # ✅ PyQt6
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)  # ✅ PyQt6
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)        # ✅ PyQt6
        self.browser.setUrl(QUrl("about:blank"))

        layout.addWidget(toolbar)
        layout.addWidget(self.browser)

        # Lancer Streamlit
        threading.Thread(target=run_streamlit, args=(self.port,), daemon=True).start()
        threading.Thread(target=self.wait_and_load, daemon=True).start()

    def wait_and_load(self):
        import urllib.request
        url = f"http://localhost:{self.port}"
        for _ in range(60):  # 30 secondes max
            try:
                urllib.request.urlopen(url, timeout=1)
                self.signals.ready.emit(self.port)
                return
            except Exception:
                time.sleep(0.5)
        self.signals.error.emit(f"Streamlit n'a pas démarré sur le port {self.port}.")

    def on_streamlit_ready(self, port: int):
        self.browser.setUrl(QUrl(f"http://localhost:{port}"))
        self.status_label.setText(f"✅ Streamlit actif — port {port}")
        self.status_label.setStyleSheet("color: #66ff99; font-size: 11px;")

    def on_streamlit_error(self, msg: str):
        self.status_label.setText(f"❌ {msg}")
        self.status_label.setStyleSheet("color: #ff6666; font-size: 11px;")

    def reload_view(self):
        self.browser.reload()


if __name__ == "__main__":
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.webenginecontext.info=false"

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())  # ✅ PyQt6 : exec() sans underscore