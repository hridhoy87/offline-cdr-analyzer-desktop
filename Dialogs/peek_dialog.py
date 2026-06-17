from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QFileDialog, QMessageBox
import pandas as pd

class TelemetryPeekDialog(QDialog):
    def __init__(self, parent, rows_data):
        super().__init__(parent)
        self.setWindowTitle("👁️ Quick Telemetry Matrix Inspection Viewport")
        self.resize(850, 500)
        self.data = rows_data
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("👁️ Live Preview: Top Processed Target Logs"))
        hdr.addStretch()
        btn_save = QPushButton("💾 Save List Separately")
        btn_save.clicked.connect(self.save_peek_separately)
        hdr.addWidget(btn_save)
        layout.addLayout(hdr)

        headers = ["Timestamp Array", "A Suspect ID", "B Contact Destination", "Activity Freq", "Primary Sector Address"]
        self.table = QTableWidget(len(self.data), len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, record in enumerate(self.data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(record.get("dt", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(record.get("ap", ""))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(record.get("bp", ""))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("freq", ""))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(record.get("loc", ""))))

        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)

    def save_peek_separately(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Preview Logs", "Preview_Logs.csv", "CSV Files (*.csv)")
        if file_path:
            try:
                df = pd.DataFrame(self.data)
                df.to_csv(file_path, index=False, encoding="utf-8")
                QMessageBox.information(self, "Success", "Log collection exported separately.")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))