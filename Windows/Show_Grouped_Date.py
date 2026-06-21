import json
import os
import pandas as pd
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QWidget, 
                             QStackedWidget, QHeaderView, QAbstractItemView, QScrollArea, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QCoreApplication, QTimer

class ShowGroupedDateWindow(QDialog):
    def __init__(self, cache_dir_or_data=None, alias_database=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chronological Location Analysis by Date")
        self.setMinimumSize(950, 700)
        
        self.cache_path = os.path.join(os.path.expanduser("~"), ".cdr_analyzer_cache", "grouped_locations.json")
        self.alias_database = alias_database if alias_database is not None else {}
        self.flat_export_data = [] 
        
        self.init_ui()
        # 💡 FIX: Removed self.load_cache_content() from here so the window doesn't freeze before opening!

    def _format_target_cdr(self, number):
        num_str = str(number).strip()
        if num_str in self.alias_database: return f"📌 {self.alias_database[num_str]} [{num_str}]"
        return num_str

    def init_ui(self):
        self.master_stack = QStackedWidget(self)
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_loading = QLabel("Inflating Spatial-Temporal Records Array...\nPlease wait. This may take a moment for large datasets.", self)
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff;")
        loading_layout.addWidget(self.lbl_loading)
        self.master_stack.addWidget(self.loading_widget)

        self.data_widget = QWidget()
        data_layout = QVBoxLayout(self.data_widget)
        
        action_bar = QHBoxLayout()
        self.btn_export = QPushButton("📤 Export Chronological Sheet Logs", self)
        self.btn_export.setMinimumHeight(35)
        self.btn_export.setStyleSheet("QPushButton { background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-weight: bold; padding: 0px 15px; } QPushButton:hover { background-color: #30363d; border-color: #8b949e; }")
        self.btn_export.clicked.connect(self.export_to_excel)
        action_bar.addWidget(self.btn_export)
        action_bar.addStretch()
        data_layout.addLayout(action_bar)
        
        self.tables_scroll_area = QScrollArea(self)
        self.tables_scroll_area.setWidgetResizable(True)
        self.tables_scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #0d1117; }")
        
        self.tables_container = QWidget()
        self.tables_vertical_layout = QVBoxLayout(self.tables_container)
        self.tables_vertical_layout.setSpacing(25)  
        self.tables_vertical_layout.setContentsMargins(0, 10, 0, 10)
        
        self.tables_scroll_area.setWidget(self.tables_container)
        data_layout.addWidget(self.tables_scroll_area)
        self.master_stack.addWidget(self.data_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.master_stack)
        self.setLayout(main_layout)
        
        # 💡 Ensure the loading screen is the first thing the user sees
        self.master_stack.setCurrentWidget(self.loading_widget)

    def load_cache_content(self):
        """LAZY LOAD: Reads the cached JSON map directly from the hard drive."""
        self.master_stack.setCurrentWidget(self.loading_widget)
        QCoreApplication.processEvents() # Force the UI to draw the loading screen
        
        try:
            records = []
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r', encoding='utf-8') as f: 
                    records = json.load(f)

            if not records:
                self.show_empty_state("No structural logs found within selected timeline boundaries.")
                return
            
            while self.tables_vertical_layout.count():
                item = self.tables_vertical_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            
            self.flat_export_data.clear()
            
            for idx, date_node in enumerate(records):
                # 💡 FIX: Keep UI from freezing during massive iteration loops
                if idx % 5 == 0:
                    QCoreApplication.processEvents() 

                current_date = date_node.get("date", "Unknown Date")
                date_flat_rows = []
                for cdr_node in date_node.get("data", []):
                    current_cdr = cdr_node.get("cdr", "N/A")
                    display_cdr = self._format_target_cdr(current_cdr)
                    
                    for loc_node in cdr_node.get("loc-data", []):
                        start = loc_node.get("start_time", "N/A")
                        end = loc_node.get("end_time", "N/A")
                        time_window = f"{start} to {end}" if start != end else start
                        
                        row_map = { "cdr_display": display_cdr, "time_window": time_window, "lac": loc_node.get("lac", "--"), "cell": loc_node.get("cell", "--"), "location": loc_node.get("address", "--") }
                        date_flat_rows.append(row_map)
                        
                        self.flat_export_data.append({
                            "Log Date": current_date, "Target A-Party": current_cdr, "Assigned Identity Alias": self.alias_database.get(current_cdr, "Unassigned Profile"),
                            "Duration Window Interval": time_window, "LAC": row_map["lac"], "Cell ID": row_map["cell"], "Identified BTS Tower Location": row_map["location"]
                        })
                            
                if not date_flat_rows: continue

                date_header_frame = QWidget()
                date_header_layout = QHBoxLayout(date_header_frame)
                date_header_layout.setContentsMargins(0, 5, 0, 2)
                lbl_date_title = QLabel(f"📅 Log Timeline Group: {current_date}")
                lbl_date_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #ffb86c;")
                date_header_layout.addWidget(lbl_date_title)
                date_header_layout.addStretch()
                self.tables_vertical_layout.addWidget(date_header_frame)

                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels(["Target A-Party", "Duration Window", "LAC", "Cell ID", "Identified BTS Cell Locations"])
                table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
                table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                table.setAlternatingRowColors(True)
                table.setRowCount(len(date_flat_rows))
                table.setStyleSheet("QTableWidget { background-color: #161b22; color: #c9d1d9; gridline-color: #30363d; border: 1px solid #30363d; border-radius: 6px; } QHeaderView::section { background-color: #21262d; color: #58a6ff; font-weight: bold; padding: 6px; border: 1px solid #30363d; }")
                
                header = table.horizontalHeader()
                for i in range(4): header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
                
                for row_idx, item in enumerate(date_flat_rows):
                    table.setItem(row_idx, 0, QTableWidgetItem(item["cdr_display"]))
                    table.setItem(row_idx, 1, QTableWidgetItem(item["time_window"]))
                    table.setItem(row_idx, 2, QTableWidgetItem(item["lac"]))
                    table.setItem(row_idx, 3, QTableWidgetItem(item["cell"]))
                    table.setItem(row_idx, 4, QTableWidgetItem(item["location"]))
                    for col in range(4): table.item(row_idx, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                total_table_rows = len(date_flat_rows)
                r = 0
                while r < total_table_rows:
                    span_len = 1
                    while ((r + span_len) < total_table_rows and date_flat_rows[r]["cdr_display"] == date_flat_rows[r + span_len]["cdr_display"]): span_len += 1
                    if span_len > 1: table.setSpan(r, 0, span_len, 1)
                    r += span_len

                r = 0
                while r < total_table_rows:
                    span_len = 1
                    while ((r + span_len) < total_table_rows and date_flat_rows[r]["cdr_display"] == date_flat_rows[r + span_len]["cdr_display"] and date_flat_rows[r]["time_window"] == date_flat_rows[r + span_len]["time_window"]): span_len += 1
                    if span_len > 1: table.setSpan(r, 1, span_len, 1)
                    r += span_len

                table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                
                table_height = table.horizontalHeader().height() + 4
                for row_idx in range(total_table_rows): table_height += table.rowHeight(row_idx)
                table.setMinimumHeight(min(table_height, 400))
                self.tables_vertical_layout.addWidget(table)
            
            self.tables_vertical_layout.addStretch()
            self.master_stack.setCurrentWidget(self.data_widget)
            
        except Exception as e:
            self.show_empty_state(f"Inflation Exception Triggered:\n{str(e)}")

    def export_to_excel(self):
        if not self.flat_export_data:
            QMessageBox.warning(self, "Export Staging Error", "No forensic records are populated to export.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Export Chronological Timeline Sheet", "Chronological_Location_Spans.xlsx", "Excel Workbooks (*.xlsx)")
        if not save_path: return

        try:
            df = pd.DataFrame(self.flat_export_data)
            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Timeline Spans")
                worksheet = writer.sheets["Timeline Spans"]
                for row in worksheet.iter_rows(min_row=2):
                    for cell in row: cell.number_format = "@"
                for col in worksheet.columns:
                    max_len = max(len(str(cell.value or '')) for cell in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

            QMessageBox.information(self, "Export Success", f"Spreadsheet logs written successfully:\n{os.path.basename(save_path)}")
        except Exception as e: QMessageBox.critical(self, "Export Crash", f"Excel Engine failed:\n{str(e)}")

    def show_empty_state(self, status_msg):
        self.lbl_loading.setText(status_msg)
        self.lbl_loading.setStyleSheet("font-size: 12pt; color: #ff5555;")
        self.master_stack.setCurrentWidget(self.loading_widget)