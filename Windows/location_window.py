import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel

class SameLocationWindow(QWidget):
    def __init__(self, raw_json_str, alias_database=None):
        super().__init__()
        self.setWindowTitle("📍 Same Location Overlap Analysis Matrix")
        self.resize(1150, 600)
        self.alias_db = alias_database if alias_database else {}
        
        layout = QVBoxLayout(self)
        records = json.loads(raw_json_str)

        if not records:
            layout.addWidget(QLabel("Analysis yielded zero concurrent spatial overlaps."))
            return

        headers = ["Time", "A Party Name / Number", "B Party Destination", "LAC", "Cell", "BTS Loc", "Match Reason"]
        table = QTableWidget(len(records), len(headers))
        table.setHorizontalHeaderLabels(headers)

        for row_idx, record in enumerate(records):
            a_raw = str(record.get("A_Party", ""))
            b_raw = str(record.get("B_Party", ""))
            
            # Map values dynamically using database lookups
            a_display = f"📌 {self.alias_db[a_raw]} [{a_raw}]" if a_raw in self.alias_db else a_raw
            b_display = f"📌 {self.alias_db[b_raw]} [{b_raw}]" if b_raw in self.alias_db else b_raw

            table.setItem(row_idx, 0, QTableWidgetItem(str(record.get("Time", ""))))
            table.setItem(row_idx, 1, QTableWidgetItem(a_display))
            table.setItem(row_idx, 2, QTableWidgetItem(b_display))
            table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("LAC", ""))))
            table.setItem(row_idx, 4, QTableWidgetItem(str(record.get("Cell", ""))))
            table.setItem(row_idx, 5, QTableWidgetItem(str(record.get("BTS_Loc", ""))))
            table.setItem(row_idx, 6, QTableWidgetItem(str(record.get("Reason", ""))))

        table.resizeColumnsToContents()
        layout.addWidget(table)