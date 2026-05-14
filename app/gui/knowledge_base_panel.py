from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.rag.vector_store import VectorStore
from app.workers.index_worker import IndexWorker


class KnowledgeBasePanel(QWidget):
    index_ready = pyqtSignal(bool)

    def __init__(self, vector_store: VectorStore, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(260)
        self.setMaximumWidth(340)

        self._vector_store = vector_store
        self._pdf_paths: list[str] = []
        self._index_worker: IndexWorker | None = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(8)

        header = QLabel("Knowledge Base")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("+ Add PDFs")
        self._add_btn.clicked.connect(self._on_add_pdfs)
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        layout.addLayout(btn_row)

        self._list_widget = QListWidget()
        self._list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._list_widget)

        self._build_btn = QPushButton("Build Index")
        self._build_btn.clicked.connect(self._on_build_index)
        layout.addWidget(self._build_btn)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("No index loaded")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._token_label = QLabel("")
        self._token_label.setObjectName("statusLabel")
        self._token_label.setWordWrap(True)
        layout.addWidget(self._token_label)

    # ── Public ────────────────────────────────────────────────────────────

    def restore_pdf_paths(self, paths: list[str]):
        for p in paths:
            if Path(p).exists() and p not in self._pdf_paths:
                self._pdf_paths.append(p)
                self._add_list_item(p)

    def get_pdf_paths(self) -> list[str]:
        return list(self._pdf_paths)

    def mark_index_loaded(self, chunk_count: int, manifest: list[dict]):
        self._status_label.setObjectName("successLabel")
        self._status_label.setText(f"Index ready — {chunk_count} chunks")
        for entry in manifest:
            fname = entry.get("file", "")
            pages = entry.get("pages", "?")
            chunks = entry.get("chunks", "?")
            item = QListWidgetItem(f"  {fname}  ({pages} pages, {chunks} chunks)")
            self._list_widget.addItem(item)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
        self.index_ready.emit(True)
        self._update_token_estimate()

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_add_pdfs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)"
        )
        for p in paths:
            if p not in self._pdf_paths:
                self._pdf_paths.append(p)
                self._add_list_item(p)
        self._update_token_estimate()

    def _on_remove(self):
        row = self._list_widget.currentRow()
        if row < 0:
            return
        self._list_widget.takeItem(row)
        if row < len(self._pdf_paths):
            self._pdf_paths.pop(row)
        self._update_token_estimate()

    def _on_build_index(self):
        if not self._pdf_paths:
            self._status_label.setText("Add PDFs first.")
            return
        if self._index_worker and self._index_worker.isRunning():
            return

        self._build_btn.setEnabled(False)
        self._add_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setObjectName("statusLabel")
        self._status_label.setText("Starting...")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

        self._index_worker = IndexWorker(self._pdf_paths, self._vector_store)
        self._index_worker.progress.connect(self._on_progress)
        self._index_worker.finished.connect(self._on_index_finished)
        self._index_worker.start()

    def _on_progress(self, msg: str):
        self._status_label.setText(msg)

    def _on_index_finished(self, success: bool, message: str):
        self._progress.setVisible(False)
        self._build_btn.setEnabled(True)
        self._add_btn.setEnabled(True)
        if success:
            self._status_label.setObjectName("successLabel")
            self._status_label.setText(f"Index ready — {len(self._vector_store.chunks)} chunks")
            self._update_token_estimate()
            self.index_ready.emit(True)
        else:
            self._status_label.setObjectName("errorLabel")
            self._status_label.setText(message)
            self.index_ready.emit(False)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _add_list_item(self, path: str):
        name = Path(path).name
        item = QListWidgetItem(f"  {name}")
        item.setToolTip(path)
        self._list_widget.addItem(item)

    def _update_token_estimate(self):
        n = len(self._pdf_paths)
        if n == 0:
            self._token_label.setText("")
            return
        est_tokens = n * 50 * 250
        self._token_label.setText(f"~{est_tokens:,} tokens est. ({n} file{'s' if n != 1 else ''})")
