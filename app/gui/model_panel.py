from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from app.cost_tracker import format_cost
from app.gui.theme import PROVIDER_COLORS


class ModelPanel(QFrame):
    """Self-contained widget for one AI model's response."""

    def __init__(self, model_config: dict, parent=None):
        super().__init__(parent)
        self._config = model_config
        self._model_id = model_config["id"]
        self._provider = model_config["provider"]
        self._full_text = ""
        self._ground_truth: str = ""
        self._in_tokens = 0
        self._out_tokens = 0
        self._cost = 0.0
        self._elapsed = 0.0
        self._citations: list[str] = []
        self._tick = 0

        self.setObjectName("modelPanel")
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 280)

        self._build_ui()
        self._setup_spinner()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        header = QWidget(self)
        header.setObjectName("panelHeader")
        color = PROVIDER_COLORS.get(self._provider, "#45475A")
        header.setStyleSheet(f"QWidget#panelHeader {{ background-color: {color}; border-radius: 7px 7px 0 0; }}")
        header.setFixedHeight(46)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 4, 10, 4)
        header_layout.setSpacing(8)

        self._checkbox = QCheckBox()
        self._checkbox.setChecked(True)
        self._checkbox.setToolTip("Enable/disable this model")
        self._checkbox.setStyleSheet("QCheckBox::indicator { border-color: rgba(255,255,255,0.6); } QCheckBox::indicator:checked { background-color: rgba(255,255,255,0.9); border-color: white; }")

        name_label = QLabel(self._config["display_name"])
        name_label.setStyleSheet("color: white; font-weight: 700; font-size: 13px; background: transparent;")
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        provider_label = QLabel(self._provider.upper())
        provider_label.setStyleSheet("color: rgba(255,255,255,0.75); font-size: 10px; font-weight: 600; background: transparent;")

        self._spinner_label = QLabel("●")
        self._spinner_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 14px; background: transparent;")
        self._spinner_label.setVisible(False)

        header_layout.addWidget(self._checkbox)
        header_layout.addWidget(name_label)
        header_layout.addWidget(provider_label)
        header_layout.addWidget(self._spinner_label)

        layout.addWidget(header)

        # ── Response area ──────────────────────────────────────────────────
        self._text_edit = QTextEdit(self)
        self._text_edit.setObjectName("responseArea")
        self._text_edit.setReadOnly(True)
        self._text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._text_edit)

        # ── Footer ────────────────────────────────────────────────────────
        footer = QWidget(self)
        footer.setObjectName("panelFooter")
        footer.setFixedHeight(36)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 4, 8, 4)
        footer_layout.setSpacing(12)

        self._time_label = QLabel("Time: --")
        self._time_label.setObjectName("statusLabel")
        self._cost_label = QLabel("Cost: --")
        self._cost_label.setObjectName("statusLabel")
        self._tokens_label = QLabel("Tokens: --")
        self._tokens_label.setObjectName("statusLabel")
        self._sources_label = QLabel("Sources: --")
        self._sources_label.setObjectName("statusLabel")
        self._sources_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        footer_layout.addWidget(self._time_label)
        footer_layout.addWidget(self._cost_label)
        footer_layout.addWidget(self._tokens_label)
        footer_layout.addWidget(self._sources_label)

        layout.addWidget(footer)

    def _setup_spinner(self):
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_chars = ["◐", "◓", "◑", "◒"]

    def _tick_spinner(self):
        self._tick = (self._tick + 1) % len(self._spinner_chars)
        self._spinner_label.setText(self._spinner_chars[self._tick])

    # ── Public interface ───────────────────────────────────────────────────

    @property
    def is_enabled(self) -> bool:
        return self._checkbox.isChecked()

    def set_enabled_checkbox(self, enabled: bool):
        self._checkbox.setChecked(enabled)

    def connect_enabled_changed(self, callback):
        self._checkbox.stateChanged.connect(callback)

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def full_text(self) -> str:
        return self._full_text

    @property
    def citations(self) -> list[str]:
        return self._citations

    def set_citations(self, citations: list[str]):
        self._citations = citations
        if citations:
            self._sources_label.setText("Sources: " + " | ".join(citations))
        else:
            self._sources_label.setText("Sources: --")

    def set_ground_truth(self, text: str):
        self._ground_truth = text.strip()

    def start_querying(self):
        self._full_text = ""
        self._text_edit.clear()
        self._time_label.setText("Time: ...")
        self._cost_label.setText("Cost: ...")
        self._tokens_label.setText("Tokens: ...")
        self._spinner_label.setVisible(True)
        self._spinner_timer.start(180)
        self.setProperty("matched", None)
        self.style().unpolish(self)
        self.style().polish(self)

    @pyqtSlot(str)
    def append_token(self, token: str):
        self._full_text += token
        self._text_edit.moveCursor(self._text_edit.textCursor().End)
        self._text_edit.insertPlainText(token)
        sb = self._text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())

    @pyqtSlot(int, int, float, float)
    def on_finished(self, in_tokens: int, out_tokens: int, elapsed: float, cost: float):
        self._in_tokens = in_tokens
        self._out_tokens = out_tokens
        self._elapsed = elapsed
        self._cost = cost
        self._spinner_timer.stop()
        self._spinner_label.setVisible(False)
        self._time_label.setText(f"Time: {elapsed:.1f}s")
        self._cost_label.setText(f"Cost: {format_cost(cost)}")
        self._tokens_label.setText(f"Tokens: {in_tokens}↑ {out_tokens}↓")
        if self._ground_truth:
            self._run_ground_truth_check()

    @pyqtSlot(str)
    def show_error(self, message: str):
        self._spinner_timer.stop()
        self._spinner_label.setVisible(False)
        self._text_edit.setStyleSheet("QTextEdit#responseArea { color: #F38BA8; background-color: #11111B; border: none; font-family: 'Consolas', monospace; font-size: 12px; padding: 8px; }")
        self._text_edit.setPlainText(f"ERROR\n\n{message}")
        self._time_label.setText("Time: --")
        self._cost_label.setText("Cost: --")
        self._tokens_label.setText("Tokens: --")

    def reset(self):
        self._full_text = ""
        self._citations = []
        self._ground_truth = ""
        self._text_edit.setStyleSheet("")
        self._text_edit.clear()
        self._time_label.setText("Time: --")
        self._cost_label.setText("Cost: --")
        self._tokens_label.setText("Tokens: --")
        self._sources_label.setText("Sources: --")
        self._spinner_timer.stop()
        self._spinner_label.setVisible(False)
        self.setProperty("matched", None)
        self.style().unpolish(self)
        self.style().polish(self)

    def get_export_data(self) -> dict:
        return {
            "model_id": self._model_id,
            "provider": self._provider,
            "display_name": self._config["display_name"],
            "response": self._full_text,
            "elapsed_s": self._elapsed,
            "cost_usd": self._cost,
            "in_tokens": self._in_tokens,
            "out_tokens": self._out_tokens,
            "sources": "; ".join(self._citations),
        }

    def _run_ground_truth_check(self):
        gt_words = set(w.lower() for w in self._ground_truth.split() if len(w) > 3)
        resp_words = set(w.lower() for w in self._full_text.split() if len(w) > 3)
        if not gt_words:
            return
        overlap = len(gt_words & resp_words) / len(gt_words)
        matched = overlap >= 0.25
        self.setProperty("matched", "true" if matched else "false")
        self.style().unpolish(self)
        self.style().polish(self)
