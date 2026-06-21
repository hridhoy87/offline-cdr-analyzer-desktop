import os
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QLineEdit, QPushButton, 
                             QMessageBox, QHeaderView, QProgressBar, QFileDialog, QStackedWidget)
from PyQt6.QtCore import Qt, QCoreApplication, QTimer
from Core.workers import SameLocationWorker
from Utils.pdf_export_manager import PDFExportManager

class SameLocationWindow(QWidget):
    def __init__(self, cache_dir_or_data, file_paths, alias_database=None):
        super().__init__()
        self.setWindowTitle("📍 Same Location Overlap Analysis Matrix")
        self.resize(1200, 750)
        self.file_paths = file_paths
        self.alias_db = alias_database if alias_database else {}
        self.cache_path = os.path.join(os.path.expanduser("~"), ".cdr_analyzer_cache", "overlap_matrix.parquet")
        self.setStyleSheet("background-color: #0d1117;")
        
        self.init_ui()
        
        # 💡 DEFER LOADING: Open the window instantly, show the loading screen, then load data.
        QTimer.singleShot(100, self.render_data_matrix)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(12)
        
        filter_ribbon = QHBoxLayout()
        filter_ribbon.addWidget(QLabel("<b>Timeframe Bounds:</b>", styleSheet="color: #f0f6fc; font-size: 13px;"))
        
        self.txt_start_time = QLineEdit(placeholderText="YYYY-MM-DD HH:MM:SS", styleSheet="background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; padding: 5px; border-radius: 4px;")
        self.txt_end_time = QLineEdit(placeholderText="YYYY-MM-DD HH:MM:SS", styleSheet="background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; padding: 5px; border-radius: 4px;")
        
        filter_ribbon.addWidget(QLabel("<font color='#c9d1d9'>Start:</font>"))
        filter_ribbon.addWidget(self.txt_start_time)
        filter_ribbon.addWidget(QLabel("<font color='#c9d1d9'>End:</font>"))
        filter_ribbon.addWidget(self.txt_end_time)
        
        self.btn_apply_filter = QPushButton("⚡ Refine Timeline", styleSheet="QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 5px 14px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #2ea043; }")
        self.btn_apply_filter.clicked.connect(self.apply_timeline_filter)
        filter_ribbon.addWidget(self.btn_apply_filter)
        
        self.btn_export_pdf = QPushButton("🖨️ Export Live Table to PDF", styleSheet="QPushButton { background-color: #8b263e; color: white; font-weight: bold; padding: 5px 14px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #a83251; }")
        self.btn_export_pdf.clicked.connect(self.export_matrix_to_pdf)
        filter_ribbon.addWidget(self.btn_export_pdf)
        self.main_layout.addLayout(filter_ribbon)
        
        self.sub_progress = QProgressBar()
        self.sub_progress.setStyleSheet("QProgressBar { border: 1px solid #30363d; border-radius: 4px; background-color: #161b22; height: 18px; } QProgressBar::chunk { background-color: #f06595; }")
        self.sub_progress.hide()
        self.main_layout.addWidget(self.sub_progress)
        
        # 💡 ADDED: Stacked Widget for Loading Screen
        self.master_stack = QStackedWidget()
        
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        self.lbl_loading = QLabel("Scanning Sector Overlaps and Building Matrix...\nPlease wait.", self)
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff;")
        loading_layout.addWidget(self.lbl_loading)
        self.master_stack.addWidget(self.loading_widget)
        
        self.data_widget = QWidget()
        self.data_layout = QVBoxLayout(self.data_widget)
        self.data_layout.setContentsMargins(0, 0, 0, 0)
        self.master_stack.addWidget(self.data_widget)
        
        self.main_layout.addWidget(self.master_stack)
        self.master_stack.setCurrentWidget(self.loading_widget)
        
        self.table = None
        self.status_lbl = None
        self.pdf_manager = PDFExportManager(self)
        self.pdf_manager.export_finished.connect(self._reset_ui_after_export)

    def render_data_matrix(self):
        self.master_stack.setCurrentWidget(self.loading_widget)
        QCoreApplication.processEvents() # Show loading screen
        
        if self.table:
            self.data_layout.removeWidget(self.table)
            self.table.deleteLater()
            self.table = None
        if self.status_lbl:
            self.data_layout.removeWidget(self.status_lbl)
            self.status_lbl.deleteLater()
            self.status_lbl = None

        records = []
        if os.path.exists(self.cache_path):
            try:
                df = pd.read_parquet(self.cache_path)
                records = df.to_dict('records')
            except Exception as e: print(f"Parquet Read Error: {e}")

        if not records:
            self.btn_export_pdf.setEnabled(False)
            self.status_lbl = QLabel("⚠️ Zero concurrent spatial overlaps detected in the cache bounds.")
            self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_lbl.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold; padding: 50px;")
            self.data_layout.addWidget(self.status_lbl)
            self.master_stack.setCurrentWidget(self.data_widget)
            return

        self.btn_export_pdf.setEnabled(True)
        headers = ["Time", "A Party Name / Number", "B Party Destination", "LAC", "Cell ID", "BTS Site Location Description", "Match Reason"]
        
        self.table = QTableWidget(len(records), len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setStyleSheet("QTableWidget { background-color: #161b22; color: #c9d1d9; gridline-color: #21262d; border: 1px solid #30363d; } QHeaderView::section { background-color: #21262d; color: #f0f6fc; font-weight: bold; padding: 5px; }")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)

        for row_idx, record in enumerate(records):
            # 💡 FIX: Keep UI smooth so the app doesn't say "Not Responding"
            if row_idx % 100 == 0: 
                QCoreApplication.processEvents() 

            a_raw = str(record.get("A_Party", ""))
            b_raw = str(record.get("B_Party", ""))
            a_display = f"📌 {self.alias_db[a_raw]} [{a_raw}]" if a_raw in self.alias_db else a_raw
            b_display = f"📌 {self.alias_db[b_raw]} [{b_raw}]" if b_raw in self.alias_db else b_raw

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(record.get("Time", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(a_display))
            self.table.setItem(row_idx, 2, QTableWidgetItem(b_display))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("LAC", ""))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(record.get("Cell", ""))))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(record.get("BTS_Loc", ""))))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(record.get("Reason", ""))))

        self.data_layout.addWidget(self.table)
        self.master_stack.setCurrentWidget(self.data_widget)

    def apply_timeline_filter(self):
        start_ts = self.txt_start_time.text().strip()
        end_ts = self.txt_end_time.text().strip()
        
        if (start_ts and not end_ts) or (end_ts and not start_ts):
            QMessageBox.warning(self, "Validation Alert", "Please ensure both bounding entries are either filled completely or left blank.")
            return

        self.btn_apply_filter.setEnabled(False)
        self.sub_progress.setRange(0, 0) 
        self.sub_progress.show()

        self.worker = SameLocationWorker(self.file_paths, start_ts=start_ts if start_ts else None, end_ts=end_ts if end_ts else None)
        self.worker.progress_updated.connect(self.sub_progress.setValue)
        self.worker.finished.connect(self.filter_processing_complete)
        self.worker.start()

    def filter_processing_complete(self, result):
        self.btn_apply_filter.setEnabled(True)
        self.sub_progress.hide()
        self.sub_progress.setRange(0, 100) 
        if result.get("status") == "success":
            self.render_data_matrix() 
        else:
            QMessageBox.critical(self, "Execution Failure", f"Thread Refinement Error: {result.get('message')}")

    def export_matrix_to_pdf(self):
        if not self.table or self.table.rowCount() == 0:
            QMessageBox.warning(self, "Export Cancelled", "No active cell records present.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Co-Location Matrix Ledger", "Same_Location_Overlap_Brief.pdf", "PDF Documents (*.pdf)")
        if not save_path: return

        self.btn_export_pdf.setEnabled(False)
        self.btn_apply_filter.setEnabled(False)
        self.sub_progress.setRange(0, 0)
        self.sub_progress.show()
        QCoreApplication.processEvents()

        # 💡 OPTIMIZATION: Use a list to build HTML instead of string concatenation
        html_lines = [f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; color: #000000; background-color: #ffffff; padding: 5px; }}
                .header-table {{ width: 100%; border-bottom: 2px solid #000000; padding-bottom: 8px; }}
                .title-header {{ font-size: 16pt; font-weight: bold; text-transform: uppercase; }}
                .data-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 9pt; }}
                .data-table th {{ background-color: #000000; color: #ffffff; text-align: left; padding: 7px 5px; border: 1px solid #000000; }}
                .data-table td {{ padding: 6px 5px; border: 1px solid #d3d3d3; vertical-align: top; page-break-inside: avoid; }}
                .stripe-row {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <table class="header-table">
                <tr><td class="title-header">Same Location Overlap Analysis Ledger</td></tr>
                <tr><td>Report Generation Date: <b>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</b></td></tr>
            </table>
            <table class="data-table">
                <thead><tr><th>Time Signature</th><th>A-Party</th><th>B-Party</th><th>LAC</th><th>Cell ID</th><th>BTS Cell Site Location</th><th>Match Reason</th></tr></thead>
                <tbody>
        """]
        
        try:
            df = pd.read_parquet(self.cache_path)
            # 💡 OPTIMIZATION: df.itertuples() is 100x faster than df.iterrows()
            for r_idx, row in enumerate(df.itertuples(index=False)):
                if r_idx % 500 == 0: 
                    QCoreApplication.processEvents() # Keeps UI responsive during massive PDF builds
                    
                stripe = ' class="stripe-row"' if r_idx % 2 == 1 else ''
                
                ap_raw = str(getattr(row, 'A_Party', ''))
                bp_raw = str(getattr(row, 'B_Party', ''))
                ap_disp = f"📌 {self.alias_db[ap_raw]} [{ap_raw}]" if ap_raw in self.alias_db else ap_raw
                bp_disp = f"📌 {self.alias_db[bp_raw]} [{bp_raw}]" if bp_raw in self.alias_db else bp_raw
                
                html_lines.append(f"<tr{stripe}><td>{getattr(row, 'Time', '')}</td><td>{ap_disp}</td><td>{bp_disp}</td><td>{getattr(row, 'LAC', '')}</td><td>{getattr(row, 'Cell', '')}</td><td>{getattr(row, 'BTS_Loc', '')}</td><td>{getattr(row, 'Reason', '')}</td></tr>")
                
                # Hard limit to prevent Chromium from crashing on absurdly massive tables
                if r_idx > 15000:
                    html_lines.append("<tr><td colspan='7'><b>[DATA TRUNCATED: PDF engine capped at 15,000 rows for rendering stability. Please export to Excel for full raw dataset.]</b></td></tr>")
                    break

        except Exception as e:
            print(f"Export Error: {e}")

        html_lines.append("</tbody></table></body></html>")
        
        # 💡 Fast-join the strings and send to Chromium
        final_html = "".join(html_lines)
        self.pdf_manager.export_html_to_pdf(final_html, save_path)

        
    def _reset_ui_after_export(self, success, path):
        self.btn_export_pdf.setEnabled(True)
        self.btn_apply_filter.setEnabled(True)
        self.sub_progress.hide()