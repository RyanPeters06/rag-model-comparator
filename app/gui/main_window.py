from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QScrollArea, QSizePolicy, QSplitter, QVBoxLayout, QWidget,
)

from app.config import get_api_key, EXPORTS_DIR, SETTINGS_FILE
from app.gui.knowledge_base_panel import KnowledgeBasePanel
from app.gui.model_panel import ModelPanel
from app.gui.query_bar import QueryBar
from app.models import MODEL_REGISTRY
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore
from app.workers.model_worker import ModelWorker

logger = logging.getLogger(__name__)

GRID_COLS = 3
WIDE_PANEL_WIDTH = 420   # px per panel in full-height / wide mode


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plant Maintenance AI Model Comparison")
        self.resize(1600, 1000)

        self._workers: list[ModelWorker] = []
        self._active_workers = 0
        self._last_question = ""
        self._full_height_mode = False

        # Which model IDs are currently shown (all visible by default)
        self._visible_ids: set[str] = {m["id"] for m in MODEL_REGISTRY}

        # RAG components
        self._vector_store = VectorStore()
        self._retriever: Retriever | None = None

        self._build_ui()
        self._load_settings()
        self._check_rag_index()
        self._show_missing_key_warning()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Warning banner
        self._warning_banner = QLabel("")
        self._warning_banner.setObjectName("warningLabel")
        self._warning_banner.setAlignment(Qt.AlignCenter)
        self._warning_banner.setStyleSheet(
            "QLabel { background-color: #3D2B00; padding: 6px; font-size: 12px; color: #FAB387; }"
        )
        self._warning_banner.setVisible(False)
        self._warning_banner.mousePressEvent = lambda _: self._warning_banner.setVisible(False)
        root_layout.addWidget(self._warning_banner)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        root_layout.addWidget(splitter)

        # ── Left sidebar ──────────────────────────────────────────────────
        self._kb_panel = KnowledgeBasePanel(self._vector_store)
        self._kb_panel.index_ready.connect(self._on_index_ready)
        self._kb_panel.paths_changed.connect(self._save_settings)
        splitter.addWidget(self._kb_panel)

        # ── Right content area ────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._query_bar = QueryBar()
        self._query_bar.send_requested.connect(self._on_send_all)
        self._query_bar.clear_requested.connect(self._on_clear_all)
        self._query_bar.export_requested.connect(self._on_export_results)
        self._query_bar.settings_requested.connect(self._show_settings_dialog)
        self._query_bar.layout_toggled.connect(self._on_layout_toggle)
        right_layout.addWidget(self._query_bar)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #313244;")
        right_layout.addWidget(sep)

        # Scroll area — content rebuilt by _rebuild_panel_area()
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        right_layout.addWidget(self._scroll_area)

        # Create all panels once (never recreated, just reparented)
        self._panels: list[ModelPanel] = []
        for cfg in MODEL_REGISTRY:
            panel = ModelPanel(cfg)
            panel.connect_enabled_changed(lambda _: self._save_settings())
            self._panels.append(panel)

        self._rebuild_panel_area()

        # Status bar
        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setFixedHeight(24)
        self._status_label.setStyleSheet(
            "QLabel { background-color: #181825; padding: 2px 10px;"
            " border-top: 1px solid #313244; color: #A6ADC8; font-size: 11px; }"
        )
        right_layout.addWidget(self._status_label)

        splitter.addWidget(right)
        splitter.setSizes([290, 1310])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    # ── Panel area layout ──────────────────────────────────────────────────

    def _rebuild_panel_area(self):
        """Detach all panels and rebuild the scroll area in the current mode."""
        # Detach every panel from its current parent so we can re-parent freely
        for panel in self._panels:
            panel.setParent(None)

        visible = [p for p in self._panels if p.model_id in self._visible_ids]

        if self._full_height_mode:
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(10, 10, 10, 10)
            h.setSpacing(10)
            for panel in visible:
                panel.setFixedWidth(WIDE_PANEL_WIDTH)
                panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
                h.addWidget(panel)
            h.addStretch()
            self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            container = QWidget()
            grid = QGridLayout(container)
            grid.setContentsMargins(10, 10, 10, 10)
            grid.setSpacing(10)
            for i, panel in enumerate(visible):
                panel.setMaximumWidth(16777215)
                panel.setMinimumWidth(0)
                panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                row, col = divmod(i, GRID_COLS)
                grid.addWidget(panel, row, col)
            for col in range(GRID_COLS):
                grid.setColumnStretch(col, 1)
            self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._scroll_area.setWidget(container)

    def _on_layout_toggle(self, wide: bool):
        self._full_height_mode = wide
        self._rebuild_panel_area()
        self._save_settings()

    # ── Settings dialog ────────────────────────────────────────────────────

    def _show_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Model Settings")
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet(self.styleSheet())

        outer = QVBoxLayout(dialog)
        outer.setSpacing(10)

        outer.addWidget(QLabel("Select which AI models to display:"))

        # Scrollable area for the checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(480)
        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setSpacing(6)
        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)

        # Group by provider
        checkboxes: dict[str, QCheckBox] = {}
        providers_seen: dict[str, QGroupBox] = {}

        for cfg in MODEL_REGISTRY:
            provider = cfg["provider"]
            if provider not in providers_seen:
                group = QGroupBox(provider.upper())
                group.setLayout(QVBoxLayout())
                inner_layout.addWidget(group)
                providers_seen[provider] = group

            cb = QCheckBox(cfg["display_name"])
            cb.setChecked(cfg["id"] in self._visible_ids)
            providers_seen[provider].layout().addWidget(cb)
            checkboxes[cfg["id"]] = cb

        inner_layout.addStretch()

        # Select all / None shortcuts
        shortcut_row = QHBoxLayout()
        from PyQt5.QtWidgets import QPushButton
        select_all_btn = QPushButton("Select All")
        select_none_btn = QPushButton("Select None")
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes.values()])
        select_none_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes.values()])
        shortcut_row.addWidget(select_all_btn)
        shortcut_row.addWidget(select_none_btn)
        shortcut_row.addStretch()
        outer.addLayout(shortcut_row)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        outer.addWidget(btn_box)

        if dialog.exec_() == QDialog.Accepted:
            self._visible_ids = {mid for mid, cb in checkboxes.items() if cb.isChecked()}
            if not self._visible_ids:          # keep at least one
                self._visible_ids = {MODEL_REGISTRY[0]["id"]}
            self._rebuild_panel_area()
            self._save_settings()

    # ── Core actions ───────────────────────────────────────────────────────

    def _on_send_all(self, question: str, ground_truth: str):
        if not question.strip():
            return

        self._last_question = question

        for w in self._workers:
            if w.isRunning():
                w.terminate()
                w.wait(500)
        self._workers.clear()

        system_context = ""
        citations: list[str] = []
        page_images: list[str] = []
        if self._vector_store.is_ready:
            try:
                if self._retriever is None:
                    from app.rag.embeddings import EmbeddingModel
                    self._retriever = Retriever(self._vector_store, EmbeddingModel.get_instance())
                results = self._retriever.retrieve(question)
                system_context, citations = self._retriever.format_context(results)
                page_images = self._retriever.get_page_images(results)
            except Exception as exc:
                self._status_label.setText(f"RAG retrieval failed ({exc}) — querying without context")

        self._query_bar.show_retrieved_sources(citations)

        self._active_workers = 0

        for panel in self._panels:
            if not panel.is_enabled or panel.model_id not in self._visible_ids:
                continue
            panel.reset()
            panel.set_citations(citations)
            panel.set_ground_truth(ground_truth)
            panel.start_querying()

            cfg = next(m for m in MODEL_REGISTRY if m["id"] == panel.model_id)

            if not get_api_key(cfg["env_key"]):
                panel.show_error(
                    f"API key '{cfg['env_key']}' is not set.\n\nAdd it to your .env file and restart."
                )
                continue

            worker = ModelWorker(cfg, question, system_context, page_images)
            worker.token_received.connect(panel.append_token)
            worker.finished.connect(panel.on_finished)
            worker.finished.connect(lambda *_: self._on_worker_done())
            worker.error_occurred.connect(panel.show_error)
            worker.error_occurred.connect(lambda *_: self._on_worker_done())
            self._workers.append(worker)
            self._active_workers += 1

        self._query_bar.set_busy(True)
        self._status_label.setText(f"Querying {self._active_workers} model(s)…")

        for w in self._workers:
            w.start()

        if self._active_workers == 0:
            self._query_bar.set_busy(False)
            self._status_label.setText("No enabled models with API keys configured.")

    def _on_worker_done(self):
        self._active_workers -= 1
        if self._active_workers <= 0:
            self._active_workers = 0
            self._query_bar.set_busy(False)
            self._status_label.setText(f"Done. {len(self._workers)} model(s) queried.")

    def _on_clear_all(self):
        for w in self._workers:
            if w.isRunning():
                w.terminate()
                w.wait(300)
        self._workers.clear()
        self._active_workers = 0
        for panel in self._panels:
            panel.reset()
        self._query_bar.set_busy(False)
        self._query_bar.clear_sources()
        self._status_label.setText("Cleared.")

    def _on_export_results(self):
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.warning(self, "Export Failed", "pandas is required: pip install pandas")
            return

        rows = []
        for panel in self._panels:
            if not panel.is_enabled or panel.model_id not in self._visible_ids:
                continue
            data = panel.get_export_data()
            data["question"] = self._last_question
            rows.append(data)

        if not rows:
            QMessageBox.information(self, "Export", "No results to export yet.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = EXPORTS_DIR / f"comparison_{timestamp}.csv"

        df = pd.DataFrame(rows)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

        msg = QMessageBox(self)
        msg.setWindowTitle("Export Complete")
        msg.setText(f"Results saved to:\n{out_path}")
        msg.setIcon(QMessageBox.Information)
        open_btn = msg.addButton("Open Folder", QMessageBox.ActionRole)
        msg.addButton("OK", QMessageBox.AcceptRole)
        msg.exec_()
        if msg.clickedButton() == open_btn:
            import subprocess
            subprocess.Popen(f'explorer /select,"{out_path}"')

    def _on_index_ready(self, success: bool):
        if success:
            try:
                from app.rag.embeddings import EmbeddingModel
                self._retriever = Retriever(self._vector_store, EmbeddingModel.get_instance())
                self._status_label.setText("Knowledge base index ready.")
            except Exception as exc:
                self._status_label.setText(f"Index built but retriever failed to load: {exc}")
        self._save_settings()

    # ── Settings persistence ───────────────────────────────────────────────

    def _load_settings(self):
        if not SETTINGS_FILE.exists():
            return
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            enabled = data.get("enabled_models", {})
            for panel in self._panels:
                if panel.model_id in enabled:
                    panel.set_enabled_checkbox(enabled[panel.model_id])
            pdf_paths = data.get("pdf_paths", [])
            if pdf_paths:
                self._kb_panel.restore_pdf_paths(pdf_paths)
            visible = data.get("visible_models", None)
            if visible is not None:
                self._visible_ids = {mid for mid, v in visible.items() if v}
                if not self._visible_ids:
                    self._visible_ids = {m["id"] for m in MODEL_REGISTRY}
                self._rebuild_panel_area()
            self._full_height_mode = data.get("wide_mode", False)
            if self._full_height_mode:
                self._query_bar._layout_btn.setChecked(True)
                self._query_bar._layout_btn.setText("☰ Grid View")
                self._rebuild_panel_area()
        except Exception as exc:
            logger.warning("Could not load settings: %s", exc)

    def _save_settings(self):
        try:
            data = {
                "enabled_models": {p.model_id: p.is_enabled for p in self._panels},
                "visible_models": {m["id"]: (m["id"] in self._visible_ids) for m in MODEL_REGISTRY},
                "wide_mode": self._full_height_mode,
                "pdf_paths": self._kb_panel.get_pdf_paths(),
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.warning("Could not save settings: %s", exc)

    # ── RAG index ─────────────────────────────────────────────────────────

    def _check_rag_index(self):
        from app.config import INDEX_DIR
        loose_pdfs = [str(p) for p in INDEX_DIR.iterdir() if p.suffix.lower() == ".pdf"]
        if loose_pdfs:
            added = self._kb_panel.add_paths(loose_pdfs)
            if added:
                self._save_settings()

        if self._vector_store.load():
            manifest = self._vector_store.get_manifest()
            self._kb_panel.mark_index_loaded(len(self._vector_store.chunks), manifest)
            self._status_label.setText(
                f"Knowledge base loaded: {len(self._vector_store.chunks)} chunks"
            )
        else:
            self._kb_panel.refresh_list_no_index()

    # ── Missing-key warning ───────────────────────────────────────────────

    def _show_missing_key_warning(self):
        seen_keys: set[str] = set()
        missing: list[str] = []
        for cfg in MODEL_REGISTRY:
            k = cfg["env_key"]
            if k not in seen_keys:
                seen_keys.add(k)
                if not get_api_key(k):
                    missing.append(k)
        if missing:
            self._warning_banner.setText(
                f"Missing API keys (click to dismiss): {', '.join(missing)}  —  Add to .env file"
            )
            self._warning_banner.setVisible(True)

    # ── Close ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._save_settings()
        for w in self._workers:
            if w.isRunning():
                w.terminate()
                w.wait(500)
        super().closeEvent(event)
