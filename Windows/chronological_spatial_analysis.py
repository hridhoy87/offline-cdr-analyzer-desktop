"""
Forensic Interactive Spatial-Temporal View Deck Window.
Loads structural arrays into a sandboxed Chromium QWebEngineView panel layer.
"""
import os
import sys
import json
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

class ChronologicalSpatialAnalysisWindow(QDialog):
    def __init__(self, roadmap_data, alias_database=None, parent=None):
        super().__init__(parent)
        self.roadmap_data = roadmap_data if roadmap_data else []
        self.alias_database = alias_database if alias_database else {}
        
        self.setWindowTitle("Interactive Spatial-Temporal Route Manifest")
        self.resize(1000, 850)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        self.setStyleSheet("background-color: #0d1117;")

        # Control Navigation Action Header Ribbon
        top_ribbon = QHBoxLayout()
        info_block = QVBoxLayout()
        title = QLabel("📡 Vector Tracking Timeline Chart")
        title.setStyleSheet("color: #f0f6fc; font-size: 16px; font-weight: bold; font-family: Arial;")
        self.lbl_meta = QLabel(f"Asynchronous Route Matrix: {len(self.roadmap_data)} timeline coordinates logged.")
        self.lbl_meta.setStyleSheet("color: #8b949e; font-size: 11px;")
        info_block.addWidget(title)
        info_block.addWidget(self.lbl_meta)
        top_ribbon.addLayout(info_block)
        top_ribbon.addStretch()

        btn_pdf = QPushButton("📥 Export Route Manifest Ledger")
        btn_pdf.setStyleSheet("""
            QPushButton { background-color: #238636; color: white; border: none; font-weight: bold; border-radius: 4px; padding: 8px 16px; }
            QPushButton:hover { background-color: #2ea44f; }
        """)
        btn_pdf.clicked.connect(self.print_timeline_to_pdf_ledger)
        top_ribbon.addWidget(btn_pdf)
        layout.addLayout(top_ribbon)

        # Mount browser viewport view canvas layout container
        self.view_canvas = QWebEngineView()
        self.view_canvas.setStyleSheet("border: 1px solid #30363d; border-radius: 6px; background-color: #0d1117;")
        
        # Configure local isolation storage rules safely
        settings = self.view_canvas.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.dirname(__file__))
            
        html_url = QUrl.fromLocalFile(os.path.join(base_path, "Utils", "spatial_roadmap.html"))
        self.view_canvas.setUrl(html_url)
        
        # Wait for Chromium to fully spool up before injecting active payload arrays
        self.view_canvas.loadFinished.connect(self.inject_roadmap_payload)
        layout.addWidget(self.view_canvas)

    def inject_roadmap_payload(self):
        """Passes calculation dict frames over the localized javascript engine bridge safely."""
        json_array_payload = json.dumps(self.roadmap_data, ensure_ascii=False)
        # Call the inline web token method directly
        self.view_canvas.page().runJavaScript(f"renderRoadmapData({json_array_payload});")

    def keyPressEvent(self, event):
        """Maps F and Escape hotkeys to handle screen expansions without breaking view canvas boundaries."""
        if event.key() == Qt.Key.Key_F:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def print_timeline_to_pdf_ledger(self):
        """Prints the browser visualization out into a clean A4 dossier brief."""
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Timeline Brief", "Spatial_Route_Dossier.pdf", "PDF Documents (*.pdf)")
        if not save_path: return

        # Import the core margin vector type explicitly 
        from PyQt6.QtCore import QMarginsF
        from PyQt6.QtGui import QPageLayout, QPageSize
        
        # Use QMarginsF to structure standard 0.4 inch boundaries cleanly
        margins = QMarginsF(0.4, 0.4, 0.4, 0.4)
        
        page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            margins,
            QPageLayout.Unit.Inch
        )
        
        # Invoke vector printing directly on the active engine layer
        self.view_canvas.page().printToPdf(save_path, page_layout)
        QMessageBox.information(self, "Export Complete", f"Interactive timeline document compiled successfully:\n{save_path}")