from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class FloatingToast(QFrame):
    """
    Android Studio-style floating toast notification for background tasks.
    Automatically anchors to the bottom right of the parent layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame { background-color: rgba(22, 27, 34, 0.95); border: 1px solid #30363d; border-radius: 8px; }
        """)
        self.setFixedSize(320, 65)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        info_layout = QVBoxLayout()
        self.lbl_text = QLabel("Assembling PDF Dossier...")
        self.lbl_text.setStyleSheet("color: #f0f6fc; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Indeterminate spinning state
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar { background-color: #0d1117; border: none; } QProgressBar::chunk { background-color: #58a6ff; }")
        
        info_layout.addWidget(self.lbl_text)
        info_layout.addWidget(self.progress)
        
        layout.addLayout(info_layout)
        self.hide()

    def update_position(self, parent_widget):
        """Keeps the toast pinned to the bottom-right corner during resizes."""
        padding = 25
        self.move(parent_widget.width() - self.width() - padding, 
                  parent_widget.height() - self.height() - padding)