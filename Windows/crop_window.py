import os
import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QFileDialog, QProgressBar, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QDateTime, QTime, QDate
from Core.workers import CropWorker
from Utils.Anim.animation import apply_mac_open_animation

CROP_STYLESHEET = """
    QWidget { background-color: #0d1117; color: #c9d1d9; }
    QFrame { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }
    QLineEdit { background-color: #0d1117; color: #f0f6fc; border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-size: 13px; }
    QLineEdit:focus { border: 1px solid #58a6ff; }
    QPushButton { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-weight: bold; }
    QPushButton:hover { background-color: #30363d; border-color: #8b949e; color: #f0f6fc; }
    #BtnExecute { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #2b6cb0); color: white; border: none; font-size: 14px; }
    #BtnExecute:hover { background: #3182ce; }
"""

class CropWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✂️ Telemetry Extraction Cropper Engine")
        self.resize(550, 500)
        self.setStyleSheet(CROP_STYLESHEET)
        self.selected_files = []
        self.init_ui()

    def showEvent(self, event):
        """Trigger macOS-style entry animation when the window appears."""
        super().showEvent(event)
        apply_mac_open_animation(self)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("✂️ Segment & Filter CDR Data Matrix")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f0f6fc;")
        layout.addWidget(title)

        # Config Panel
        panel = QFrame()
        panel_layout = QVBoxLayout(panel)
        
        panel_layout.addWidget(QLabel("Geographic / Base Station Keyword Match"))
        self.input_loc = QLineEdit()
        self.input_loc.setPlaceholderText("e.g. Dhaka, Tower Name, LAC Code...")
        panel_layout.addWidget(self.input_loc)

        # Time Pickers
        panel_layout.addWidget(QLabel("Temporal Boundaries (From)"))
        self.dt_from = QLineEdit()
        self.dt_from.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.dt_from.setText(QDateTime.currentDateTime().addDays(-7).toString("yyyy-MM-dd 00:00:00"))
        panel_layout.addWidget(self.dt_from)

        panel_layout.addWidget(QLabel("Temporal Boundaries (To)"))
        self.dt_to = QLineEdit()
        self.dt_to.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.dt_to.setText(QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"))
        panel_layout.addWidget(self.dt_to)
        
        layout.addWidget(panel)

        # File Select & Trigger Pipeline
        self.btn_select = QPushButton("📁 Stage Raw Target Files")
        self.btn_select.clicked.connect(self.select_files)
        layout.addWidget(self.btn_select)

        self.lbl_status = QLabel("Engine Ready • No files staged")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #8b949e; font-style: italic;")
        layout.addWidget(self.lbl_status)

        self.btn_run = QPushButton("⚡ Execute Slicing & Export")
        self.btn_run.setObjectName("BtnExecute")
        self.btn_run.clicked.connect(self.run_crop)
        layout.addWidget(self.btn_run)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select CDR Files", "", "Excel Files (*.xlsx)")
        if files:
            self.selected_files = files
            self.lbl_status.setText(f"Staged {len(files)} target worksheets.")
            self.lbl_status.setStyleSheet("color: #58a6ff; font-weight: bold;")

    def run_crop(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Error", "No source data staged for analysis.")
            return

        self.progress.setRange(0, 0)
        self.progress.setVisible(True)
        out_dir = os.path.expanduser("~/Documents/CDR_Reports")
        os.makedirs(out_dir, exist_ok=True)

        self.worker = CropWorker(
            self.selected_files, self.input_loc.text(), 
            self.dt_from.text(), self.dt_to.text(), out_dir
        )
        self.worker.finished.connect(self.crop_completed)
        self.worker.start()

    def crop_completed(self, result):
        self.progress.setVisible(False)
        if result["status"] == "success":
            QMessageBox.information(self, "Success", f"Cropped data packet exported:\n{result['output_path']}\n\nRows parsed: {result['count']}")
            self.lbl_status.setText(f"Exported: {os.path.basename(result['output_path'])}")
        else:
            QMessageBox.critical(self, "Engine Failure", result["message"])