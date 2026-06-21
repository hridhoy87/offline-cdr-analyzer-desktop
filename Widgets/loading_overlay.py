import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QLabel, QProgressBar, QPushButton, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class ForensicLoadingOverlay(QWidget):
    """
    Full-screen semi-transparent loading mask with optional background task routing.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0d1117;")
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.central_card = QFrame()
        self.central_card.setFixedSize(480, 320)
        self.central_card.setStyleSheet("""
            QFrame { background-color: rgba(13, 17, 23, 0.88); border: 1px solid #30363d; border-radius: 12px; }
        """)
        
        card_layout = QVBoxLayout(self.central_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(18)
        card_layout.setContentsMargins(30, 30, 30, 30)
        
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setStyleSheet("background: transparent; border: none;")
        
        if os.path.exists("logo.png"):
            pixmap = QPixmap("logo.png")
            scaled_pixmap = pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_logo.setPixmap(scaled_pixmap)
        else:
            self.lbl_logo.setText("📡")
            self.lbl_logo.setStyleSheet("font-size: 55px; background: transparent; border: none;")
            
        card_layout.addWidget(self.lbl_logo)
        
        self.lbl_status = QLabel("Initializing Forensic Subsystem Vectors...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("QLabel { color: #f0f6fc; font-size: 14px; font-weight: bold; font-family: 'Segoe UI', Arial; background: transparent; border: none; }")
        card_layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(320)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 0) 
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #30363d; border-radius: 4px; text-align: center; color: white; background-color: #161b22; height: 18px; font-size: 11px; }
            QProgressBar::chunk { background-color: #f06595; }
        """)
        card_layout.addWidget(self.progress_bar)

        self.btn_background = QPushButton("⬇️ Do it in Background")
        self.btn_background.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_background.setStyleSheet("""
            QPushButton { background: transparent; color: #8b949e; text-decoration: none; border: none; font-size: 12px; margin-top: 10px; }
            QPushButton:hover { color: #58a6ff; text-decoration: underline; }
        """)
        self.btn_background.setVisible(False)
        card_layout.addWidget(self.btn_background)

        master_layout.addWidget(self.central_card)
        self.setVisible(False)

    def trigger_loading(self, message, allow_background=False):
        self.lbl_status.setText(message)
        self.btn_background.setVisible(allow_background)
        if self.parentWidget():
            self.resize(self.parentWidget().size())
        self.setVisible(True)
        self.raise_()
        QApplication.processEvents()

    def dismiss_loading(self):
        self.setVisible(False)