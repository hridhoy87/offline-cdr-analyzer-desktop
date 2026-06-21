import os
import sys
import json
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QFileDialog, QStackedWidget, QWidget
from PyQt6.QtCore import Qt, QUrl, QMarginsF, QTimer, QCoreApplication
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

from Utils.Anim.animation import apply_mac_open_animation

class ChronologicalSpatialAnalysisWindow(QDialog):
    def __init__(self, cache_path_or_data, alias_database=None, parent=None):
        super().__init__(parent)
        
        self.cache_path = None
        self.roadmap_data = []
        self.alias_database = alias_database if alias_database else {}
        
        if isinstance(cache_path_or_data, str) and os.path.exists(cache_path_or_data):
            self.cache_path = cache_path_or_data
        elif isinstance(cache_path_or_data, list):
            self.roadmap_data = cache_path_or_data
        
        self.setWindowTitle("Interactive Spatial-Temporal Route Manifest")
        self.resize(1000, 850)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        self.setStyleSheet("background-color: #0d1117;")

        # 💡 ADDED: Master Stack for Loading Screen
        self.master_stack = QStackedWidget(self)
        
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading = QLabel("Applying Identity Aliases & Rendering Spatial Maps...\nPlease wait.", self)
        self.lbl_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading.setStyleSheet("font-size: 14pt; font-weight: bold; color: #58a6ff;")
        loading_layout.addWidget(self.lbl_loading)
        self.master_stack.addWidget(self.loading_widget)

        self.data_widget = QWidget()
        data_layout = QVBoxLayout(self.data_widget)
        data_layout.setContentsMargins(0,0,0,0)

        top_ribbon = QHBoxLayout()
        info_block = QVBoxLayout()
        title = QLabel("📡 Vector Tracking Timeline Chart")
        title.setStyleSheet("color: #f0f6fc; font-size: 16px; font-weight: bold; font-family: Arial;")
        self.lbl_meta = QLabel("Asynchronous Route Matrix: Waiting for Chromium engine...")
        self.lbl_meta.setStyleSheet("color: #8b949e; font-size: 11px;")
        info_block.addWidget(title)
        info_block.addWidget(self.lbl_meta)
        top_ribbon.addLayout(info_block)
        top_ribbon.addStretch()

        btn_pdf = QPushButton("📥 Export Route Manifest Ledger")
        btn_pdf.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; border-radius: 4px; padding: 8px 16px; } QPushButton:hover { background-color: #2ea44f; }")
        btn_pdf.clicked.connect(self.print_timeline_to_pdf_ledger)
        top_ribbon.addWidget(btn_pdf)
        data_layout.addLayout(top_ribbon)

        self.view_canvas = QWebEngineView()
        self.view_canvas.setStyleSheet("border: 1px solid #30363d; border-radius: 6px; background-color: #0d1117;")
        
        settings = self.view_canvas.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        try: base_path = sys._MEIPASS
        except Exception: base_path = os.path.dirname(os.path.dirname(__file__))
            
        html_url = QUrl.fromLocalFile(os.path.join(base_path, "Utils", "spatial_roadmap.html"))
        self.view_canvas.setUrl(html_url)
        
        # 💡 FIX: Defer injection so UI loading screen stays active
        self.view_canvas.loadFinished.connect(self.on_browser_ready)
        data_layout.addWidget(self.view_canvas)
        
        self.master_stack.addWidget(self.data_widget)
        layout.addWidget(self.master_stack)
        
        # Force the screen to show loading when window opens
        self.master_stack.setCurrentWidget(self.loading_widget)

    def on_browser_ready(self):
        # We wait 100ms so the Chromium engine gets fully painted on the screen
        QTimer.singleShot(100, self.inject_roadmap_payload)

    def inject_roadmap_payload(self):
        """Lazily loads the tracking frames, applies aliases, and passes to Chromium."""
        aliased_roadmap = []
        
        if self.cache_path and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    
                for idx, node in enumerate(raw_data):
                    if idx % 50 == 0: 
                        QCoreApplication.processEvents() # Prevent UI freeze

                    node_copy = node.copy()
                    ap_num = node_copy.get("A_Party", "")
                    bp_num = node_copy.get("B_Party", "")
                    loc_str = node_copy.get("Location", "")
                    
                    if ap_num in self.alias_database: node_copy["A_Party"] = f"📌 {self.alias_database[ap_num]} [{ap_num}]"
                    if bp_num in self.alias_database: node_copy["B_Party"] = f"📌 {self.alias_database[bp_num]} [{bp_num}]"
                        
                    for stored_num, assigned_name in self.alias_database.items():
                        if stored_num in loc_str: loc_str = loc_str.replace(stored_num, f"📌 {assigned_name} [{stored_num}]")
                    node_copy["Location"] = loc_str
                    aliased_roadmap.append(node_copy)
            except Exception as e:
                print(f"Cache load fault: {e}")
        else:
            aliased_roadmap = self.roadmap_data
            
        self.lbl_meta.setText(f"Asynchronous Route Matrix: {len(aliased_roadmap)} timeline coordinates logged.")
        
        # 💡 FIX FOR payload.forEach ERROR: Safely parse JSON natively in Javascript
        escaped = json.dumps(aliased_roadmap).replace('\\', '\\\\').replace('"', '\\"')
        js_code = f"""
            try {{
                var data = JSON.parse("{escaped}");
                if (typeof renderRoadmapData === 'function') {{
                    renderRoadmapData(data);
                }} else {{
                    console.error('renderRoadmapData function not found in HTML');
                }}
            }} catch (e) {{
                console.error('JSON parsing failed:', e);
            }}
        """
        self.view_canvas.page().runJavaScript(js_code)
        
        # Data injected, switch view away from loading screen
        self.master_stack.setCurrentWidget(self.data_widget)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def print_timeline_to_pdf_ledger(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Timeline Brief", "Spatial_Route_Dossier.pdf", "PDF Documents (*.pdf)")
        if not save_path: 
            return
        
        margins = QMarginsF(0.4, 0.4, 0.4, 0.4)
        page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            margins,
            QPageLayout.Unit.Inch
        )
        
        self.view_canvas.page().printToPdf(save_path, page_layout)
        QMessageBox.information(self, "Export Initiated", f"The PDF report is being compiled by the engine:\n{save_path}")