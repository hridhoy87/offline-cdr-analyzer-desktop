from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QCalendarWidget, QTimeEdit)
from PyQt6.QtCore import Qt, QDateTime, QDate, QTime

TIMELINE_STYLESHEET = """
    QDialog { background-color: #0d1117; border: 1px solid #30363d; }
    QLabel { color: #f0f6fc; font-size: 13px; font-weight: bold; }
    QCalendarWidget QWidget { background-color: #161b22; color: #c9d1d9; }
    QCalendarWidget QAbstractItemView:enabled { background-color: #161b22; color: #c9d1d9; selection-background-color: #1f6feb; selection-color: white; }
    QCalendarWidget QMenu { background-color: #161b22; color: #c9d1d9; }
    QTimeEdit { background-color: #161b22; color: #f0f6fc; border: 1px solid #30363d; border-radius: 4px; padding: 6px; }
    QPushButton { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
    QPushButton:hover { background-color: #30363d; border-color: #8b949e; color: #f0f6fc; }
    #BtnApply { background-color: #1f6feb; color: white; border: none; }
    #BtnApply:hover { background-color: #388bfd; }
"""

class TimelinePickerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏳ Temporal Boundary Constraints")
        self.resize(750, 420)
        self.setStyleSheet(TIMELINE_STYLESHEET)
        
        self.start_timestamp = None
        self.end_timestamp = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        columns_layout = QHBoxLayout()

        # Start Date and Time Picker Column
        left_box = QVBoxLayout()
        left_box.addWidget(QLabel("⏳ Start Boundary (From)"))
        self.cal_start = QCalendarWidget()
        self.cal_start.setGridVisible(True)
        seven_days_ago = QDateTime.currentDateTime().addDays(-7)
        self.cal_start.setSelectedDate(seven_days_ago.date())
        left_box.addWidget(self.cal_start)

        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(0, 0, 0))
        left_box.addWidget(self.time_start)
        columns_layout.addLayout(left_box)

        # End Date and Time Picker Column
        right_box = QVBoxLayout()
        right_box.addWidget(QLabel("⏳ End Boundary (To)"))
        self.cal_end = QCalendarWidget()
        self.cal_end.setGridVisible(True)
        self.cal_end.setSelectedDate(QDate.currentDate())
        right_box.addWidget(self.cal_end)

        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(23, 59, 59))
        right_box.addWidget(self.time_end)
        columns_layout.addLayout(right_box)

        main_layout.addLayout(columns_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_apply = QPushButton("Apply Timeline")
        btn_apply.setObjectName("BtnApply")
        btn_apply.clicked.connect(self.accept_selection)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_cancel)
        main_layout.addLayout(btn_layout)

    def accept_selection(self):
        date_start = self.cal_start.selectedDate().toString("yyyy-MM-dd")
        time_start = self.time_start.time().toString("HH:mm:ss")
        self.start_timestamp = f"{date_start} {time_start}"

        date_end = self.cal_end.selectedDate().toString("yyyy-MM-dd")
        time_end = self.time_end.time().toString("HH:mm:ss")
        self.end_timestamp = f"{date_end} {time_end}"
        self.accept()