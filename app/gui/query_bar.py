from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)


class QueryBar(QWidget):
    send_requested = pyqtSignal(str, str)   # question, ground_truth
    clear_requested = pyqtSignal()
    export_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    layout_toggled = pyqtSignal(bool)       # True = wide/full-height mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(170)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 6)
        layout.setSpacing(6)

        # Question input
        q_row = QHBoxLayout()
        q_label = QLabel("Question:")
        q_label.setFixedWidth(80)
        self._question_edit = QTextEdit()
        self._question_edit.setPlaceholderText(
            "Type your question here (Ctrl+Enter to send)…"
        )
        self._question_edit.setFixedHeight(68)
        self._question_edit.installEventFilter(self)
        q_row.addWidget(q_label)
        q_row.addWidget(self._question_edit)
        layout.addLayout(q_row)

        # Ground truth input
        gt_row = QHBoxLayout()
        gt_label = QLabel("Ground Truth:")
        gt_label.setFixedWidth(80)
        self._gt_edit = QLineEdit()
        self._gt_edit.setPlaceholderText("Optional: paste correct answer for accuracy scoring")
        gt_row.addWidget(gt_label)
        gt_row.addWidget(self._gt_edit)
        layout.addLayout(gt_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._send_btn = QPushButton("Send to All")
        self._send_btn.setObjectName("sendBtn")
        self._send_btn.clicked.connect(self._on_send)

        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.clicked.connect(self.clear_requested.emit)

        self._export_btn = QPushButton("Export Results")
        self._export_btn.clicked.connect(self.export_requested.emit)

        self._settings_btn = QPushButton("⚙ Models")
        self._settings_btn.setToolTip("Show / hide individual AI model panels")
        self._settings_btn.clicked.connect(self.settings_requested.emit)

        self._layout_btn = QPushButton("⊞ Wide View")
        self._layout_btn.setToolTip("Switch to full-height panels with left-right scrolling")
        self._layout_btn.setCheckable(True)
        self._layout_btn.clicked.connect(self._on_layout_toggle)

        self._sources_label = QLabel("")
        self._sources_label.setObjectName("statusLabel")
        self._sources_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        btn_row.addWidget(self._send_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addWidget(self._export_btn)
        btn_row.addWidget(self._settings_btn)
        btn_row.addWidget(self._layout_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._sources_label)
        layout.addLayout(btn_row)

    def _on_layout_toggle(self, checked: bool):
        self._layout_btn.setText("☰ Grid View" if checked else "⊞ Wide View")
        self.layout_toggled.emit(checked)

    def eventFilter(self, obj, event):
        if obj is self._question_edit:
            from PyQt5.QtCore import QEvent
            if event.type() == QEvent.KeyPress:
                ke = event
                if ke.key() == Qt.Key_Return and ke.modifiers() & Qt.ControlModifier:
                    self._on_send()
                    return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        question = self._question_edit.toPlainText().strip()
        if not question:
            return
        ground_truth = self._gt_edit.text().strip()
        self.send_requested.emit(question, ground_truth)

    def set_busy(self, busy: bool):
        self._send_btn.setEnabled(not busy)

    def show_retrieved_sources(self, citations: list[str]):
        if citations:
            self._sources_label.setText("Retrieved: " + " | ".join(citations[:3]) + ("…" if len(citations) > 3 else ""))
        else:
            self._sources_label.setText("No KB context (index empty or no match)")

    def clear_sources(self):
        self._sources_label.setText("")
