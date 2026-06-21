import os
import sys
import json
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
                             QLabel, QScrollArea, QFrame, QProgressBar, QTextBrowser, 
                             QPushButton, QFileDialog, QApplication, QMessageBox, QStyle)
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QEvent, QTimer
from PyQt6.QtGui import QKeyEvent

ANALYSIS_DASHBOARD_STYLE = """
    QWidget { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; }
    QFrame { background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; }
    #Header { font-size: 16px; font-weight: bold; color: #f0f6fc; padding: 5px; border-bottom: 1px solid #30363d; }
    QScrollArea { border: none; background-color: transparent; }
    QTextBrowser { background-color: #0d1117; border: none; color: #c9d1d9; font-size: 13px; }
"""

class LinkAnalysisWindow(QWidget):
    def __init__(self, cache_dir_or_data=None, alias_database=None):
        super().__init__()
        self.setWindowTitle("🔬 Advanced Forensic Link Analysis Deck — Press 'F' to Fullscreen, 'Esc' to Exit")
        self.resize(1450, 880)
        self.alias_db = alias_database if alias_database else {}
        self.cache_path = os.path.join(os.path.expanduser("~"), ".cdr_analyzer_cache", "graph_data.json")
        self.is_graph_fullscreen = False
        
        # 💡 LAZY LOAD: Parse JSON directly from the hard drive
        raw_dict = {}
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    raw_dict = json.load(f)
            except Exception as e: print(f"Failed to read graph cache: {e}")

        self.payload = self.inject_workspace_aliases_into_payload(raw_dict)
        
        self.setStyleSheet(ANALYSIS_DASHBOARD_STYLE)
        self.init_ui()

        qApp = QApplication.instance()
        if qApp: qApp.installEventFilter(self)

    def closeEvent(self, event):
        qApp = QApplication.instance()
        if qApp: qApp.removeEventFilter(self)
        super().closeEvent(event)

    def inject_workspace_aliases_into_payload(self, data):
        import copy
        display_data = copy.deepcopy(data)
        if "centers" in display_data:
            display_data["centers"] = [f"📌 {self.alias_db[str(c)]} [{c}]" if str(c) in self.alias_db else str(c) for c in display_data["centers"]]
        if "uncommon-links" in display_data:
            for item in display_data["uncommon-links"]:
                src = str(item["source"])
                if src in self.alias_db: item["source"] = f"📌 {self.alias_db[src]} [{src}]"
                item["target-links"] = [f"📌 {self.alias_db[str(t)]} [{t}]" if str(t) in self.alias_db else str(t) for t in item["target-links"]]
        if "common-links" in display_data:
            for item in display_data["common-links"]:
                tgt = str(item["target"])
                if tgt in self.alias_db: item["target"] = f"📌 {self.alias_db[tgt]} [{tgt}]"
                item["source"] = [f"📌 {self.alias_db[str(s)]} [{s}]" if str(s) in self.alias_db else str(s) for s in item["source"]]
        if "node_profiles" in display_data:
            updated_profiles = {}
            for node_id, profile in display_data["node_profiles"].items():
                key = f"📌 {self.alias_db[node_id]} [{node_id}]" if node_id in self.alias_db else node_id
                updated_profiles[key] = profile
            display_data["node_profiles"] = updated_profiles
        return display_data

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.setStyleSheet("QSplitter::handle { background-color: #30363d; width: 2px; }")
        
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        meta_scroll = QScrollArea()
        meta_scroll.setWidgetResizable(True)
        meta_content = QWidget()
        self.meta_layout = QVBoxLayout(meta_content)
        self.meta_layout.setSpacing(15)
        
        self.build_common_contacts_panel()
        self.build_regional_histogram()
        
        meta_scroll.setWidget(meta_content)
        left_layout.addWidget(meta_scroll)
        self.workspace_splitter.addWidget(self.left_panel)

        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.right_splitter.setStyleSheet("QSplitter::handle { background-color: #30363d; height: 2px; }")
        
        self.vp1_frame = QFrame()
        self.vp1_layout = QVBoxLayout(self.vp1_frame)
        self.lbl_graph_header = QLabel("🧬 Node Topology Intercept Model")
        self.lbl_graph_header.setObjectName("Header")
        self.vp1_layout.addWidget(self.lbl_graph_header)
        
        self.browser_calls = QWebEngineView()
        settings = self.browser_calls.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.vp1_layout.addWidget(self.browser_calls)
        self.right_splitter.addWidget(self.vp1_frame)
        
        self.vp2_frame = QFrame()
        vp2_layout = QVBoxLayout(self.vp2_frame)
        lbl2 = QLabel("📱 Device & Subscriber Hardware Profile Lists")
        lbl2.setObjectName("Header")
        vp2_layout.addWidget(lbl2)
        
        self.btn_export_hw = QPushButton("💾 Save Hardware Index List Separately")
        self.btn_export_hw.clicked.connect(self.save_hw_index_separately)
        vp2_layout.addWidget(self.btn_export_hw)
        
        self.hardware_text_list = QTextBrowser()
        vp2_layout.addWidget(self.hardware_text_list)
        self.right_splitter.addWidget(self.vp2_frame)
        
        self.right_splitter.setSizes([500, 300])
        self.workspace_splitter.addWidget(self.right_splitter)
        self.workspace_splitter.setSizes([450, 1000])
        main_layout.addWidget(self.workspace_splitter)

        self.populate_hardware_text_lists()

        try: base_path = sys._MEIPASS
        except Exception: base_path = os.path.abspath(".")
        
        html_path = os.path.join(base_path, "Utils", "link_analysis.html")
        self.browser_calls.setUrl(QUrl.fromLocalFile(html_path))
        self.browser_calls.loadFinished.connect(self.inject_call_data)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_F:
                if not self.is_graph_fullscreen: self.enter_graph_fullscreen()
                return True
            elif event.key() == Qt.Key.Key_Escape:
                if self.is_graph_fullscreen: self.exit_graph_fullscreen()
                return True
        return super().eventFilter(watched, event)

    def enter_graph_fullscreen(self):
        self.is_graph_fullscreen = True
        self.left_panel.hide()
        self.lbl_graph_header.hide()
        self.vp2_frame.hide()
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.showFullScreen()
        QTimer.singleShot(250, self.force_html_canvas_resize)

    def exit_graph_fullscreen(self):
        self.is_graph_fullscreen = False
        self.left_panel.show()
        self.lbl_graph_header.show()
        self.vp2_frame.show()
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.showNormal()
        QTimer.singleShot(250, self.force_html_canvas_resize)

    def force_html_canvas_resize(self):
        self.browser_calls.page().runJavaScript("if(typeof window.dispatchEvent === 'function') { window.dispatchEvent(new Event('resize')); }")

    def inject_call_data(self, success):
        if success:
            escaped = json.dumps(self.payload).replace('\\', '\\\\').replace('"', '\\"')
            self.browser_calls.page().runJavaScript(f"window.renderOfflineData(JSON.stringify(JSON.parse(\"{escaped}\")));")

    def save_hw_index_separately(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Hardware Mapping Report", "Hardware_Profiles.html", "HTML Webpages (*.html)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f: f.write(self.hardware_text_list.toHtml())

    def build_common_contacts_panel(self):
        box = QFrame()
        vbox = QVBoxLayout(box)
        vbox.addWidget(QLabel("🎯 Identified Common Contacts Directory"))
        common_links = self.payload.get("common-links", [])
        node_profiles = self.payload.get("node_profiles", {})
        
        if not common_links:
            lbl_none = QLabel("No cross-link common contacts detected.")
            lbl_none.setStyleSheet("color: #8b949e; font-style: italic; padding: 5px;")
            vbox.addWidget(lbl_none)
        else:
            for item in common_links:
                common_b_party = item.get("target")
                shared_by_list = item.get("source", [])
                profile = node_profiles.get(str(common_b_party), {})
                total_calls = profile.get("total", "N/A")
                
                item_frame = QFrame()
                item_frame.setStyleSheet("background-color: #0d1117; border-color: #21262d; margin-top: 4px; padding: 6px;")
                f_layout = QVBoxLayout(item_frame)
                f_layout.setSpacing(2)
                
                num_lbl = QLabel(f"🔗 Shared Contact: {common_b_party}")
                num_lbl.setStyleSheet("font-weight: bold; color: #f06595; font-size: 11px;")
                
                freq_lbl = QLabel(f"Total Logged Interactions: {total_calls} calls")
                freq_lbl.setStyleSheet("font-size: 11px; color: #c9d1d9;")
                
                shared_lbl = QLabel(f"Shared By Targets: {', '.join(shared_by_list)}")
                shared_lbl.setStyleSheet("font-size: 11px; color: #58a6ff;")
                shared_lbl.setWordWrap(True)
                
                f_layout.addWidget(num_lbl); f_layout.addWidget(freq_lbl); f_layout.addWidget(shared_lbl)
                vbox.addWidget(item_frame)
        self.meta_layout.addWidget(box)

    def populate_hardware_text_lists(self):
        html_output = '<div style="font-family: sans-serif; padding: 10px; line-height: 1.5; color: #c9d1d9;"><h3 style="color: #58a6ff; border-bottom: 1px solid #30363d;">📡 SIM Profile to Device Signatures Index</h3><ul style="padding-left: 20px; margin-bottom: 25px;">'
        sim_map = self.payload.get("sim_to_imei_map", {})
        if not sim_map: html_output += "<li><i>No subscriber hardware profile linkages found.</i></li>"
        else:
            for sim, records in sim_map.items():
                sim_display = f"📌 {self.alias_db[sim]} [{sim}]" if sim in self.alias_db else sim
                html_output += f"<li style='margin-bottom: 8px;'><b style='color: #f0f6fc;'>Subscriber SIM: {sim_display}</b><br/><span style='color: #8b949e;'>Linked Signatures:</span><br/>"
                for r in records: html_output += f"&nbsp;&nbsp;• <span style='color: #ffb86c;'>IMEI: {r.get('imei', 'N/A')}</span> — <span style='color: #79c0ff;'>{r.get('hw', 'Generic Handset')}</span><br/>"
                html_output += "</li>"
        
        html_output += '</ul><h3 style="color: #f06595; border-bottom: 1px solid #30363d;">🛡️ Handset Terminal to Active SIMs List</h3><ul style="padding-left: 20px;">'
        imei_map = self.payload.get("imei_to_sim_map", {})
        if not imei_map: html_output += "<li><i>No cross-link physical device swaps observed.</i></li>"
        else:
            for imei, info in imei_map.items():
                sims_mapped = [f"📌 {self.alias_db[str(s)]} [{s}]" if str(s) in self.alias_db else str(s) for s in info.get("sims", [])]
                html_output += f"<li style='margin-bottom: 8px;'><b style='color: #f0f6fc;'>Model: {info.get('hardware', 'Generic')}</b><br/><span style='color: #8b949e;'>IMEI:</span> <span style='color: #ff79c6;'>{imei}</span><br/><span style='color: #8b949e;'>Linked SIMs:</span> <span style='color: #58a6ff;'>{', '.join(sims_mapped)}</span></li>"
        html_output += "</ul></div>"
        self.hardware_text_list.setHtml(html_output)

    def build_regional_histogram(self):
        box = QFrame()
        vbox = QVBoxLayout(box)
        vbox.addWidget(QLabel("📊 Regional Area Cluster Frequency (Top Sectors)"))
        clusters = self.payload.get("area_clusters", [])
        if clusters:
            max_hits = max([int(c['count']) for c in clusters]) if clusters else 1
            for cluster in clusters[:8]:
                row = QWidget()
                h = QHBoxLayout(row)
                h.setContentsMargins(0, 2, 0, 2)
                lbl_name = QLabel(cluster['area'])
                lbl_name.setMinimumWidth(140); lbl_name.setMaximumWidth(140)
                lbl_name.setStyleSheet("font-size: 11px; color: #8b949e;")
                bar = QProgressBar()
                bar.setRange(0, max_hits); bar.setValue(int(cluster['count'])); bar.setTextVisible(False)
                bar.setStyleSheet("QProgressBar { background-color: #161b22; border: none; height: 6px; } QProgressBar::chunk { background-color: #3182ce; }")
                lbl_count = QLabel(str(cluster['count']))
                lbl_count.setStyleSheet("font-size: 11px; font-weight: bold; color: #58a6ff;")
                h.addWidget(lbl_name); h.addWidget(bar); h.addWidget(lbl_count)
                vbox.addWidget(row)
        self.meta_layout.addWidget(box)