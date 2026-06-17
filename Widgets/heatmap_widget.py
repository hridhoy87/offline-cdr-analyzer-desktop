from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

class TemporalHeatmapWidget(QWidget):
    def __init__(self, a_party, hour_dist_dict):
        super().__init__()
        self.a_party = a_party
        self.hour_dist = hour_dist_dict
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        # Title Label
        title = QLabel(f"🕒 Base Station Activity Chronology Bar Array: {self.a_party}")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(title)

        # Grid Block Container
        blocks_layout = QHBoxLayout()
        blocks_layout.setSpacing(2)
        
        max_val = max(self.hour_dist.values()) if self.hour_dist.values() else 1

        for hour in range(24):
            count = self.hour_dist.get(str(hour), 0)
            block = QWidget()
            block.setFixedHeight(24)
            block.setMinimumWidth(12)
            
            # Interpolation logic matching Android color weights
            if count == 0:
                color_hex = "#161b22"  # Idle node color
            else:
                ratio = count / max_val
                if ratio < 0.5:
                    # Low-to-Mid traffic distribution: Green to Orange interpolation
                    g = int(174 + (196 - 174) * (ratio * 2))
                    color_hex = f"background-color: rgb(39, {g}, 96);"
                else:
                    # High-density traffic burst: Yellow to Crimson array interpolation
                    r = int(241 + (231 - 241) * ((ratio - 0.5) * 2))
                    color_hex = f"background-color: rgb({r}, 76, 60);"
            
            block.setStyleSheet(f"{color_hex} border-radius: 2px;")
            block.setToolTip(f"Hour Slot: {hour:02d}:00 | Interactions Matrix Vol: {count} logs")
            blocks_layout.addWidget(block)
            
        layout.addLayout(blocks_layout)

        # Chronology Indicator Labels Axis row
        axis_layout = QHBoxLayout()
        for marker in range(24):
            lbl = QLabel(f"{marker:02d}" if marker in [0, 6, 12, 18, 23] else "")
            lbl.setStyleSheet("font-size: 9px; color: #8b949e;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            axis_layout.addWidget(lbl)
        layout.addLayout(axis_layout)