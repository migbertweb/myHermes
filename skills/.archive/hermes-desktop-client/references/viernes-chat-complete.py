"""
Viernes Chat — Complete Working Implementation
PyQt6 floating chat window for Hermes Agent on Hyprland

Usage:
  cd ~/hermes-chat && python3 main.py

Dependencies:
  - PyQt6 (python-pyqt6 on Arch)
  - Hermes Agent CLI (hermes)
  - hyprshot (optional, for screenshot capture)

Files created in ~/hermes-chat/:
  main.py        — this file
  launch.sh      — start/focus script
  toggle.sh      — show/hide toggle for keybind
  hyprland.conf  — Hyprland window rules
"""

import sys
import subprocess
import json
import os
import tempfile

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QScrollArea, QLabel, QFrame, QToolButton,
    QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

# ── Config ──────────────────────────────────────────────────────────────────

CONFIG = {
    "window_width": 420,
    "window_height": 600,
    "opacity": 0.92,
    "border_radius": 16,
    "font_family": "sans-serif",
    "font_size_base": 13,
    "color_bg": "rgba(18, 18, 30, 0.75)",
    "color_bg_input": "rgba(30, 30, 50, 0.6)",
    "color_accent": "#7c5cfc",
    "color_accent_hover": "#9b7eff",
    "color_text": "#f0f0f5",
    "color_text_secondary": "rgba(240, 240, 245, 0.6)",
    "color_user_bubble": "rgba(124, 92, 252, 0.3)",
    "color_assistant_bubble": "rgba(40, 40, 65, 0.5)",
    "color_border": "rgba(255, 255, 255, 0.08)",
}

# ── Hermes Bridge ────────────────────────────────────────────────────────────

class HermesClient:
    """Communicates with local Hermes Agent via hermes -z (oneshot mode)."""

    def __init__(self):
        self.session_id = None
        self._load_last_session()

    def _load_last_session(self):
        try:
            result = subprocess.run(
                ["hermes", "sessions", "list", "--json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                sessions = json.loads(result.stdout)
                if sessions:
                    self.session_id = sessions[0].get("id")
        except Exception:
            pass

    def send_message(self, text: str) -> str:
        cmd = ["hermes", "-z", text]
        if self.session_id:
            cmd.extend(["--resume", self.session_id])
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            self._load_last_session()
            return result.stdout.strip() or result.stderr.strip()
        except subprocess.TimeoutExpired:
            return "*⏱️ Viernes no respondió a tiempo*"
        except FileNotFoundError:
            return "*❌ Hermes no está instalado*"
        except Exception as e:
            return f"*❌ Error: {e}*"

# ── UI Components ────────────────────────────────────────────────────────────

class MessageBubble(QFrame):
    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        bg = CONFIG["color_user_bubble"] if is_user else CONFIG["color_assistant_bubble"]
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {CONFIG["color_text"]};
                font-size: {CONFIG["font_size_base"]}px;
                padding: 10px 14px;
                background: {bg};
                border-radius: 12px;
                border: 1px solid {CONFIG["color_border"]};
            }}
        """)
        if is_user:
            layout.addStretch()
            layout.addWidget(self.label)
            self.label.setMaximumWidth(300)
        else:
            layout.addWidget(self.label)
            layout.addStretch()
            self.label.setMaximumWidth(320)


class ChatArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)
        lay.addStretch()

    def add_message(self, text: str, is_user: bool = False):
        lay = self.layout()
        lay.insertWidget(lay.count() - 1, MessageBubble(text, is_user))

    def update_last_assistant(self, text: str):
        lay = self.layout()
        for i in range(lay.count() - 2, -1, -1):
            widget = lay.itemAt(i).widget()
            if isinstance(widget, MessageBubble) and not widget.is_user:
                widget.label.setText(text)
                return

# ── Main Window ──────────────────────────────────────────────────────────────

class FloatingChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hermes = HermesClient()
        self.dragging = False
        self.drag_position = QPoint()
        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()
        self.add_welcome_message()

    def setup_window(self):
        self.setWindowTitle("Viernes Chat")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowOpacity(CONFIG["opacity"])
        QTimer.singleShot(0, self._apply_geometry)

    def _apply_geometry(self):
        self.setFixedSize(CONFIG["window_width"], CONFIG["window_height"])
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = (geom.width() - CONFIG["window_width"]) // 2
            y = (geom.height() - CONFIG["window_height"]) // 2 - 60
            self.setGeometry(x, y, CONFIG["window_width"], CONFIG["window_height"])

    def setup_ui(self):
        self._central = QFrame(self)
        self._central.setObjectName("central")
        self._central.setStyleSheet(f"""
            QFrame#central {{
                background: {CONFIG["color_bg"]};
                border-radius: {CONFIG["border_radius"]}px;
                border: 1px solid {CONFIG["color_border"]};
            }}
        """)
        self.setCentralWidget(self._central)
        layout = QVBoxLayout(self._central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        bar = QFrame()
        bar.setFixedHeight(40)
        bar.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(10, 0, 10, 0)
        btn_close = QToolButton()
        btn_close.setFixedSize(28, 28)
        btn_close.setText("✕")
        btn_close.setStyleSheet(f"""
            QToolButton {{ color: {CONFIG["color_text_secondary"]}; background: transparent;
                border: none; font-size: 14px; border-radius: 14px; }}
            QToolButton:hover {{ background: rgba(255, 80, 80, 0.3); color: #ff5555; }}
        """)
        btn_close.clicked.connect(self.hide)
        hl.addWidget(btn_close)
        hl.addStretch()
        title = QLabel("Viernes")
        title.setStyleSheet(f"color: {CONFIG['color_text']}; font-size: 13px; font-weight: 600; background: transparent;")
        hl.addWidget(title)
        hl.addStretch()
        btn_new = QToolButton()
        btn_new.setFixedSize(28, 28)
        btn_new.setText("↻")
        btn_new.setStyleSheet(f"""
            QToolButton {{ color: {CONFIG["color_text_secondary"]}; background: transparent;
                border: none; font-size: 16px; border-radius: 14px; }}
            QToolButton:hover {{ background: rgba(255,255,255,0.1); color: {CONFIG["color_text"]}; }}
        """)
        btn_new.clicked.connect(self.new_chat)
        hl.addWidget(btn_new)
        layout.addWidget(bar)

        layout.addWidget(self._sep())
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 6px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); border-radius: 3px; }
        """)
        self._chat = ChatArea()
        self._scroll_area.setWidget(self._chat)
        layout.addWidget(self._scroll_area, 1)
        layout.addWidget(self._sep())
        layout.addWidget(self._create_input_bar())

    def _sep(self):
        s = QFrame()
        s.setFixedHeight(1)
        s.setStyleSheet(f"background: {CONFIG['color_border']};")
        return s

    def _create_input_bar(self):
        container = QFrame()
        container.setStyleSheet("background: transparent;")
        container.setFixedHeight(120)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 12)
        layout.setSpacing(6)

        actions = QHBoxLayout()
        for icon, tip, cb in [
            ("📎", "Adjuntar", lambda: self._attach()),
            ("🌐", "Web", None),
            ("📷", "Capturar", lambda: self._capture()),
        ]:
            btn = QToolButton()
            btn.setText(icon); btn.setToolTip(tip)
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"""
                QToolButton {{ color: {CONFIG["color_text_secondary"]}; background: transparent;
                    border: none; font-size: 16px; border-radius: 15px; }}
                QToolButton:hover {{ background: rgba(255,255,255,0.1); }}
            """)
            if cb: btn.clicked.connect(cb)
            actions.addWidget(btn)
        actions.addStretch()
        lbl = QLabel("deepseek-v4-flash")
        lbl.setStyleSheet(f"color: {CONFIG['color_text_secondary']}; font-size: 10px; background: transparent; padding: 2px 8px;")
        actions.addWidget(lbl)
        layout.addLayout(actions)

        input_row = QHBoxLayout()
        self._input = QTextEdit()
        self._input.setPlaceholderText("Pregúntale algo a Viernes...")
        self._input.setFixedHeight(40)
        self._input.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background: {CONFIG["color_bg_input"]}; color: {CONFIG["color_text"]};
                border: 1px solid {CONFIG["color_border"]}; border-radius: 12px;
                padding: 8px 14px; font-size: {CONFIG["font_size_base"]}px;
            }}
            QTextEdit:focus {{ border: 1px solid {CONFIG["color_accent"]}; }}
        """)
        input_row.addWidget(self._input, 1)

        self._btn_send = QPushButton("↑")
        self._btn_send.setFixedSize(36, 36)
        self._btn_send.setStyleSheet(f"""
            QPushButton {{ background: {CONFIG["color_accent"]}; color: white;
                border: none; border-radius: 18px; font-size: 18px; font-weight: bold; }}
            QPushButton:hover {{ background: {CONFIG["color_accent_hover"]}; }}
        """)
        self._btn_send.clicked.connect(self.send_message)
        input_row.addWidget(self._btn_send)
        layout.addLayout(input_row)
        return container

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Return"), self).activated.connect(self.send_message)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.hide)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and not event.modifiers():
            self.send_message()
            return
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self._input.insertPlainText("\n")
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 40:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_position)
            self.drag_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    # ── Actions ──

    def add_welcome_message(self):
        self._chat.add_message(
            "✨ <b>¡Hola! Soy Viernes.</b><br><br>"
            "Pregúntame lo que quieras. Puedo buscar en la web, "
            "leer archivos, ejecutar comandos y mucho más.",
            is_user=False
        )

    def send_message(self):
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._chat.add_message(text, is_user=True)
        self._input.clear()
        self._chat.add_message("...🧠 <i>Pensando</i>", is_user=False)
        self._scroll_to_bottom()
        self._btn_send.setEnabled(False)
        self._btn_send.setText("⏳")
        QTimer.singleShot(50, lambda: self._process(text))

    def _process(self, text: str):
        response = self.hermes.send_message(text)
        self._chat.update_last_assistant(response)
        self._scroll_to_bottom()
        self._btn_send.setEnabled(True)
        self._btn_send.setText("↑")

    def _scroll_to_bottom(self):
        sb = self._scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def new_chat(self):
        self.hermes.session_id = None
        lay = self._chat.layout()
        while lay.count():
            w = lay.takeAt(0).widget()
            if w: w.deleteLater()
        self.add_welcome_message()

    def _attach(self):
        path, _ = QFileDialog.getOpenFileName(self, "Adjuntar archivo")
        if path:
            self._input.setText(f"[Archivo: {path}]")

    def _capture(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        try:
            subprocess.Popen(["hyprshot", "-m", "region", "-o", tmp.name],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._input.setText(f"[Captura: {tmp.name}]")
        except FileNotFoundError:
            self._input.setText("[hyprshot no instalado]")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont(CONFIG["font_family"], CONFIG["font_size_base"]))
    w = FloatingChatWindow()
    w.show()
    sys.exit(app.exec())
