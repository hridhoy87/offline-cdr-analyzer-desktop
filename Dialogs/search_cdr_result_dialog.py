import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextBrowser, QApplication
from PyQt6.QtCore import Qt

DIALOG_STYLESHEET = """
    QDialog {
        background-color: #0d1117;
        border: 1px solid #30363d;
    }
    QLabel {
        color: #f0f6fc;
        font-size: 15px;
        font-weight: bold;
    }
    QTextBrowser {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
        color: #c9d1d9;
        font-size: 13px;
        line-height: 1.6;
    }
    QPushButton {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #30363d;
        border-color: #8b949e;
        color: #f0f6fc;
    }
    #BtnCopyShare {
        background-color: #1f6feb;
        color: #ffffff;
        border: none;
    }
    #BtnCopyShare:hover {
        background-color: #388bfd;
    }
"""

class SearchCdrResultDialog(QDialog):
    def __init__(self, parent, summary_html):
        super().__init__(parent)
        self.setWindowTitle("🔎 Cross-Column Search Hits Matrix")
        self.resize(700, 500)
        self.summary_html = summary_html
        self.setStyleSheet(DIALOG_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_lbl = QLabel("🔎 Forensic Query Search Results")
        layout.addWidget(title_lbl)

        self.browser = QTextBrowser()
        self.browser.setHtml(self.summary_html)
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser)

        info_lbl = QLabel("💡 Tip: Click 'Copy Report' to snapshot plain text to your clipboard.")
        info_lbl.setStyleSheet("color: #8b949e; font-size: 11px; font-weight: normal; font-style: italic;")
        layout.addWidget(info_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_copy = QPushButton("📋 Copy Report")
        self.btn_copy.setObjectName("BtnCopyShare")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        
        self.btn_close = QPushButton("Close Viewport")
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_copy)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def copy_to_clipboard(self):
        plain_text = self.browser.toPlainText()
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(plain_text)
            self.btn_copy.setText("✅ Copied!")
            self.btn_copy.setEnabled(False)