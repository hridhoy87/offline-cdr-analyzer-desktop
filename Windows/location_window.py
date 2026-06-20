import json
import os
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QLabel, QLineEdit, QPushButton, \
                             QMessageBox, QHeaderView, QProgressBar, QFileDialog)
from PyQt6.QtCore import Qt, QMarginsF, QCoreApplication
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
# FIXED: Imported QPrinter matching your proven pdf_report_writer.py engine implementation
from PyQt6.QtPrintSupport import QPrinter
from Core.workers import SameLocationWorker

class SameLocationWindow(QWidget):
    def __init__(self, raw_json_str, file_paths, alias_database=None):
        """
        Initializes the dynamic standalone co-location monitoring matrix sub-panel.
        
        :param raw_json_str: Initial collection of intersection arrays encoded as a JSON string.
        :param file_paths: Historical tracking logs (points directly to MainWindow.selected_files).
        :param alias_database: Active identity dictionary lookup framework (MainWindow.phone_aliases).
        """
        super().__init__()
        self.setWindowTitle("📍 Same Location Overlap Analysis Matrix")
        self.resize(1200, 750)
        
        # Store file metrics and identity aliases for internal re-filtering runs
        self.file_paths = file_paths
        self.alias_db = alias_database if alias_database else {}
        
        # Base window vertical structure container layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(12)
        self.setStyleSheet("background-color: #0d1117;") # Dark theme framework background alignment
        
        # --- SUB-PANEL OPERATIONAL CONTROLLER RIBBON ---
        filter_ribbon = QHBoxLayout()
        
        lbl_title = QLabel("<b>Timeframe Bounds:</b>")
        lbl_title.setStyleSheet("color: #f0f6fc; font-size: 13px;")
        filter_ribbon.addWidget(lbl_title)
        
        filter_ribbon.addWidget(QLabel("<font color='#c9d1d9'>Start:</font>"))
        self.txt_start_time = QLineEdit()
        self.txt_start_time.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.txt_start_time.setStyleSheet(
            "background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; "
            "padding: 5px; border-radius: 4px; font-family: Consolas;"
        )
        filter_ribbon.addWidget(self.txt_start_time)
        
        filter_ribbon.addWidget(QLabel("<font color='#c9d1d9'>End:</font>"))
        self.txt_end_time = QLineEdit()
        self.txt_end_time.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        self.txt_end_time.setStyleSheet(
            "background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; "
            "padding: 5px; border-radius: 4px; font-family: Consolas;"
        )
        filter_ribbon.addWidget(self.txt_end_time)
        
        # Action Buttons
        self.btn_apply_filter = QPushButton("⚡ Refine Timeline")
        self.btn_apply_filter.setStyleSheet(
            "QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 5px 14px; border-radius: 4px; border: none; }"
            "QPushButton:hover { background-color: #2ea043; }"
            "QPushButton:disabled { background-color: #21262d; color: #8b949e; }"
        )
        self.btn_apply_filter.clicked.connect(self.apply_timeline_filter)
        filter_ribbon.addWidget(self.btn_apply_filter)
        
        self.btn_export_pdf = QPushButton("🖨️ Export Live Table to PDF")
        self.btn_export_pdf.setStyleSheet(
            "QPushButton { background-color: #8b263e; color: white; font-weight: bold; padding: 5px 14px; border-radius: 4px; border: none; }"
            "QPushButton:hover { background-color: #a83251; }"
            "QPushButton:disabled { background-color: #21262d; color: #8b949e; }"
        )
        self.btn_export_pdf.clicked.connect(self.export_matrix_to_pdf)
        filter_ribbon.addSpacing(10)
        filter_ribbon.addWidget(self.btn_export_pdf)
        
        self.main_layout.addLayout(filter_ribbon)
        
        # --- GRANULAR INTERNAL STATUS LOADER COMPONENT ---
        self.sub_progress = QProgressBar()
        self.sub_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #30363d; border-radius: 4px; text-align: center; color: white; background-color: #161b22; height: 18px; font-size: 11px; }
            QProgressBar::chunk { background-color: #f06595; }
        """)
        self.sub_progress.hide()
        self.main_layout.addWidget(self.sub_progress)
        
        # Interactive Layout Element Placeholders
        self.table = None
        self.status_lbl = None
        
        # Initial compilation layout rendering call pass
        self.render_data_matrix(raw_json_str)

    def render_data_matrix(self, json_data_str):
        """Clears out stale grid objects and draws the updated multi-suspect intersection rows."""
        if self.table:
            self.main_layout.removeWidget(self.table)
            self.table.deleteLater()
            self.table = None
        if self.status_lbl:
            self.main_layout.removeWidget(self.status_lbl)
            self.status_lbl.deleteLater()
            self.status_lbl = None

        try:
            records = json.loads(json_data_str)
        except Exception:
            records = []

        if not records:
            self.btn_export_pdf.setEnabled(False)
            self.status_lbl = QLabel("⚠️ The defined operational constraints yielded zero concurrent spatial overlaps.")
            self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_lbl.setStyleSheet("color: #ff6b6b; font-size: 14px; font-weight: bold; padding: 50px;")
            self.main_layout.addWidget(self.status_lbl)
            return

        self.btn_export_pdf.setEnabled(True)
        headers = ["Time", "A Party Name / Number", "B Party Destination", "LAC", "Cell ID", "BTS Site Location Description", "Match Reason"]
        
        self.table = QTableWidget(len(records), len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #161b22; color: #c9d1d9; gridline-color: #21262d; border: 1px solid #30363d; border-radius: 4px; }
            QHeaderView::section { background-color: #21262d; color: #f0f6fc; border: 1px solid #30363d; font-weight: bold; padding: 5px; }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)

        for row_idx, record in enumerate(records):
            a_raw = str(record.get("A_Party", ""))
            b_raw = str(record.get("B_Party", ""))
            
            # Formulate aliased label structures securely using stored cross-case maps
            a_display = f"📌 {self.alias_db[a_raw]} [{a_raw}]" if a_raw in self.alias_db else a_raw
            b_display = f"📌 {self.alias_db[b_raw]} [{b_raw}]" if b_raw in self.alias_db else b_raw

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(record.get("Time", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(a_display))
            self.table.setItem(row_idx, 2, QTableWidgetItem(b_display))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("LAC", ""))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(record.get("Cell", ""))))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(record.get("BTS_Loc", ""))))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(record.get("Reason", ""))))

        self.main_layout.addWidget(self.table)

    def apply_timeline_filter(self):
        """Spins up an isolated asynchronous worker to recalculate location data loops under the custom bounds."""
        start_ts = self.txt_start_time.text().strip()
        end_ts = self.txt_end_time.text().strip()
        
        if (start_ts and not end_ts) or (end_ts and not start_ts):
            QMessageBox.warning(self, "Validation Alert", "Please ensure both bounding entries are either filled completely or left blank.")
            return

        self.btn_apply_filter.setEnabled(False)
        self.btn_export_pdf.setEnabled(False)
        self.sub_progress.setRange(0, 0) # Trigger an indefinite pulsing wait state animation
        self.sub_progress.show()

        # Allocate background tasking vectors
        self.worker = SameLocationWorker(self.file_paths)
        self.worker.start_ts = start_ts if start_ts else None
        self.worker.end_ts = end_ts if end_ts else None
        
        # Tie communication signal-slots safely
        self.worker.progress_updated.connect(self.sub_progress.setValue)
        self.worker.finished.connect(self.filter_processing_complete)
        self.worker.start()

    def filter_processing_complete(self, result):
        """Fires upon thread execution completion loops, resetting tracking animations and updating the UI layout grid."""
        self.btn_apply_filter.setEnabled(True)
        self.sub_progress.hide()
        self.sub_progress.setRange(0, 100) # Reset tracking bounds explicitly

        if result.get("status") == "success":
            self.render_data_matrix(result.get("data", "[]"))
        else:
            QMessageBox.critical(self, "Execution Failure", f"Thread Refinement Error: {result.get('message')}")

    def export_matrix_to_pdf(self):
        """Translates the active screen table records into a landscape monochromatic corporate dossier intelligence brief."""
        if not self.table or self.table.rowCount() == 0:
            QMessageBox.warning(self, "Export Cancelled", "No active cell records present within the workspace layout grids to format.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Co-Location Matrix Ledger", "Same_Location_Overlap_Brief.pdf", "PDF Documents (*.pdf)"
        )
        if not save_path:
            return

        # Initialize full printing loading state mask overlays immediately
        self.btn_export_pdf.setEnabled(False)
        self.btn_apply_filter.setEnabled(False)
        self.sub_progress.setRange(0, 0)
        self.sub_progress.show()
        QCoreApplication.processEvents() # Force standard thread context refresh to draw loading bar instantly

        # High-contrast printing layout CSS specs blocks definitions
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: 'Arial', sans-serif; color: #000000; background-color: #ffffff; padding: 5px; }
                .header-table { width: 100%; margin-bottom: 25px; border-bottom: 2px solid #000000; padding-bottom: 8px; }
                .title-header { font-size: 16pt; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
                .confidential-tag { text-align: right; color: #ff0000; font-weight: bold; font-size: 11pt; letter-spacing: 1px; }
                .meta-text { font-size: 10pt; color: #333333; line-height: 1.4; }
                
                .data-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 9pt; }
                .data-table th { background-color: #000000; color: #ffffff; font-weight: bold; text-align: left; padding: 7px 5px; border: 1px solid #000000; }
                .data-table td { padding: 6px 5px; border: 1px solid #d3d3d3; vertical-align: top; }
                .stripe-row { background-color: #f8f9fa; }
            </style>
        </head>
        <body>
            <table class="header-table">
                <tr>
                    <td class="title-header">Same Location Overlap Analysis Ledger</td>
                    <td class="confidential-tag">LAW ENFORCEMENT SENSITIVE</td>
                </tr>
                <tr>
                    <td class="meta-text">
                        <b>Compiled Workspace Logs:</b> Analysis extracted from localized cross-case records.<br/>
                        <b>Timestamp Range Window:</b> Dynamic runtime bounds constraints applied.<br/>
                        <b>Total Concurrent Overlaps Isolated:</b> TOTAL_COUNT_ROWS
                    </td>
                    <td class="meta-text" style="text-align: right; vertical-align: bottom;">
                        Report Generation Date:<br/><b>""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</b>
                    </td>
                </tr>
            </table>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 13%;">Time Signature</th>
                        <th style="width: 18%;">A-Party Identifier</th>
                        <th style="width: 18%;">B-Party Destination</th>
                        <th style="width: 7%;">LAC</th>
                        <th style="width: 7%;">Cell ID</th>
                        <th style="width: 23%;">BTS Cell Site Location Description</th>
                        <th style="width: 14%;">Match Reason</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Populate rows cleanly by reading straight from the current visual grid widgets
        row_count = self.table.rowCount()
        for r_idx in range(row_count):
            stripe_class = ' class="stripe-row"' if r_idx % 2 == 1 else ''
            html_content += f"<tr{stripe_class}>"
            for c_idx in range(7):
                cell_item = self.table.item(r_idx, c_idx)
                cell_txt = cell_item.text() if cell_item else ""
                
                # Protect deep nested numbers containing bracketed tags from string layout clipping
                if c_idx in [1, 2] and len(cell_txt) > 20:
                    cell_txt = cell_txt.replace(" [", "<br/>[")
                    
                html_content += f"<td>{cell_txt}</td>"
            html_content += "</tr>"

        html_content = html_content.replace("TOTAL_COUNT_ROWS", str(row_count))
        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """

        try:
            doc = QTextDocument()
            doc.setHtml(html_content)
            
            # FIXED: Instantiated QPrinter engine objects following the working pattern of pdf_report_writer.py
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(save_path)
            
            margins = QMarginsF(0.5, 0.5, 0.5, 0.5)
            layout = QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Landscape, 
                margins,
                QPageLayout.Unit.Inch
            )
            printer.setPageLayout(layout)
            
            # Render document to the printer object securely to build the file
            doc.print(printer)
            
            # Clear loading mask blocks ONLY when the investigator dismisses the tracking confirmation panel
            QMessageBox.information(self, "Export Finalized", f"Pristine vector brief saved successfully at:\n{os.path.normpath(save_path)}")
        except Exception as ex:
            QMessageBox.critical(self, "Export Failure", f"Failed to parse or write landscape template layout to disk:\n{str(ex)}")
        finally:
            # Safely reclaim button invocation states
            self.btn_export_pdf.setEnabled(True)
            self.btn_apply_filter.setEnabled(True)
            self.sub_progress.hide()
            self.sub_progress.setRange(0, 100)