from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.rag.vector_store import VectorStore
from app.workers.index_worker import IndexWorker


class KnowledgeBasePanel(QWidget):
    index_ready = pyqtSignal(bool)
    paths_changed = pyqtSignal()   # fires whenever the PDF list is modified

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

        self._add_folder_btn = QPushButton("+ Add Folder")
        self._add_folder_btn.setToolTip("Scan a folder and add all PDFs inside it")
        self._add_folder_btn.clicked.connect(self._on_add_folder)
        layout.addWidget(self._add_folder_btn)

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
        """Called on startup from saved settings. Populates _pdf_paths only —
        list widget is populated later by mark_index_loaded with full info."""
        for p in paths:
            if Path(p).exists() and p not in self._pdf_paths:
                self._pdf_paths.append(p)
        # Don't touch the list widget here; mark_index_loaded will do it
        # with richer info (page counts). If no index exists, _refresh_list
        # is called explicitly after this.

    def get_pdf_paths(self) -> list[str]:
        return list(self._pdf_paths)

    def mark_index_loaded(self, chunk_count: int, manifest: list[dict]):
        """Called on startup when a saved index is found. Replaces the list
        widget contents with manifest data (has page + chunk counts)."""
        self._refresh_list(manifest)
        self._set_status(f"Index ready — {chunk_count} chunks", "successLabel")
        self.index_ready.emit(True)
        self._update_token_estimate()

    def refresh_list_no_index(self):
        """Call after restore_pdf_paths when no saved index exists, so the
        list widget still shows the restored filenames."""
        self._refresh_list(manifest=[])

    # ── Slots ─────────────────────────────────────────────────────────────

    def add_paths(self, paths: list[str]) -> int:
        """Add a list of absolute PDF paths. Returns count of newly added files."""
        added = 0
        for p in paths:
            if p not in self._pdf_paths and Path(p).exists():
                self._pdf_paths.append(p)
                added += 1
        if added:
            self._refresh_list(self._vector_store.get_manifest())
            self._update_token_estimate()
            self.paths_changed.emit()
        return added

    def _on_add_pdfs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)"
        )
        self.add_paths(paths)

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing PDFs")
        if not folder:
            return
        found = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() == ".pdf"]
        added = self.add_paths(found)
        if added:
            self._set_status(f"Added {added} PDF(s) from folder", "successLabel")
        else:
            self._set_status("No new PDFs found in that folder", "statusLabel")

    def _on_remove(self):
        row = self._list_widget.currentRow()
        if row < 0:
            return
        self._list_widget.takeItem(row)
        if row < len(self._pdf_paths):
            self._pdf_paths.pop(row)
        self._update_token_estimate()
        self.paths_changed.emit()

    def _on_build_index(self):
        if not self._pdf_paths:
            self._set_status("Add PDFs first.", "statusLabel")
            return
        if self._index_worker and self._index_worker.isRunning():
            return

        self._build_btn.setEnabled(False)
        self._add_btn.setEnabled(False)
        self._add_folder_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._set_status("Starting...", "statusLabel")

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
        self._add_folder_btn.setEnabled(True)
        if success:
            # Refresh list with up-to-date page/chunk counts from the new manifest
            self._refresh_list(self._vector_store.get_manifest())
            chunk_count = len(self._vector_store.chunks)
            self._set_status(f"Index ready — {chunk_count} chunks", "successLabel")
            self._update_token_estimate()
            self.index_ready.emit(True)
        else:
            self._set_status(message, "errorLabel")
            self.index_ready.emit(False)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _refresh_list(self, manifest: list[dict]):
        """Rebuild the list widget from _pdf_paths, annotating with manifest
        data where available. Clears first to prevent duplicates."""
        manifest_map = {entry["file"]: entry for entry in manifest}
        self._list_widget.clear()
        for path in self._pdf_paths:
            name = Path(path).name
            entry = manifest_map.get(name)
            if entry:
                label = f"  {name}  ({entry.get('pages','?')} pages, {entry.get('chunks','?')} chunks)"
            else:
                label = f"  {name}  (not yet indexed)"
            item = QListWidgetItem(label)
            item.setToolTip(path)
            self._list_widget.addItem(item)

    def _set_status(self, text: str, obj_name: str):
        self._status_label.setObjectName(obj_name)
        self._status_label.setText(text)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _update_token_estimate(self):
        n = len(self._pdf_paths)
        if n == 0:
            self._token_label.setText("")
            return
        # RAG only sends the top-5 retrieved chunks per query, not the whole library.
        # 5 chunks × 500 words × ~0.75 tokens/word ≈ 1,875 tokens injected per query.
        self._token_label.setText(
            f"{n} PDF{'s' if n != 1 else ''} loaded  •  ~1,875 tokens injected per query"
        )
