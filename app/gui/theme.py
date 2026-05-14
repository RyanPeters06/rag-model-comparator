PROVIDER_COLORS = {
    "anthropic":  "#C4622D",
    "openai":     "#19C37D",
    "google":     "#4285F4",
    "deepseek":   "#5B9BD5",
    "mistral":    "#F5A623",
    "xai":        "#8B5CF6",
    "openrouter": "#FF6B35",
}

DARK_STYLESHEET = """
QWidget {
    background-color: #1E1E2E;
    color: #CDD6F4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #1E1E2E;
}

QSplitter::handle {
    background-color: #313244;
    width: 2px;
}

/* ── Scroll areas ── */
QScrollArea {
    border: none;
    background-color: #1E1E2E;
}
QScrollBar:vertical {
    background: #181825;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #45475A;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #585B70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #181825;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #45475A;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover { background: #585B70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Text inputs ── */
QTextEdit, QPlainTextEdit, QLineEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px 8px;
    color: #CDD6F4;
    selection-background-color: #45475A;
}
QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {
    border: 1px solid #89B4FA;
}

/* ── Buttons ── */
QPushButton {
    background-color: #313244;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 6px 14px;
    color: #CDD6F4;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #45475A;
    border-color: #585B70;
}
QPushButton:pressed {
    background-color: #585B70;
}
QPushButton:disabled {
    background-color: #1E1E2E;
    color: #585B70;
    border-color: #313244;
}

QPushButton#sendBtn {
    background-color: #1E6B4A;
    border-color: #19C37D;
    color: #CDD6F4;
    font-weight: 600;
    padding: 8px 20px;
}
QPushButton#sendBtn:hover {
    background-color: #19C37D;
    color: #1E1E2E;
}
QPushButton#sendBtn:pressed {
    background-color: #158F59;
}
QPushButton#sendBtn:disabled {
    background-color: #1E1E2E;
    border-color: #313244;
    color: #585B70;
}

/* ── Labels ── */
QLabel {
    color: #CDD6F4;
}
QLabel#sectionHeader {
    font-size: 14px;
    font-weight: 700;
    color: #89B4FA;
    padding: 4px 0;
}
QLabel#statusLabel {
    color: #A6ADC8;
    font-size: 12px;
    padding: 2px 8px;
}
QLabel#errorLabel {
    color: #F38BA8;
    font-size: 12px;
}
QLabel#successLabel {
    color: #A6E3A1;
    font-size: 12px;
}
QLabel#warningLabel {
    color: #FAB387;
    font-size: 12px;
}

/* ── List widget ── */
QListWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    color: #CDD6F4;
}
QListWidget::item {
    padding: 4px 6px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #45475A;
}
QListWidget::item:hover {
    background-color: #313244;
}

/* ── Progress bar ── */
QProgressBar {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 4px;
    text-align: center;
    color: #CDD6F4;
    height: 12px;
    font-size: 11px;
}
QProgressBar::chunk {
    background-color: #89B4FA;
    border-radius: 4px;
}

/* ── Checkboxes ── */
QCheckBox {
    spacing: 6px;
    color: #CDD6F4;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #45475A;
    background-color: #181825;
}
QCheckBox::indicator:checked {
    background-color: #89B4FA;
    border-color: #89B4FA;
}
QCheckBox::indicator:hover {
    border-color: #89B4FA;
}

/* ── Model panel frame ── */
QFrame#modelPanel {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
}
QFrame#modelPanel[matched="true"] {
    border: 2px solid #A6E3A1;
}
QFrame#modelPanel[matched="false"] {
    border: 2px solid #F38BA8;
}

/* ── Panel header ── */
QWidget#panelHeader {
    border-radius: 7px 7px 0 0;
}

/* ── Response text area ── */
QTextEdit#responseArea {
    background-color: #11111B;
    border: none;
    border-radius: 0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    color: #CDD6F4;
    padding: 8px;
}

/* ── Panel footer ── */
QWidget#panelFooter {
    background-color: #181825;
    border-top: 1px solid #313244;
    border-radius: 0 0 7px 7px;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}

/* ── Tooltip ── */
QToolTip {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
