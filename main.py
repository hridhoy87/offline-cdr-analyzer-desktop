import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLineEdit, QLabel, 
                             QFileDialog, QProgressBar, QTextBrowser, QMessageBox,
                             QFrame, QScrollArea, QSplitter, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTreeView)
from PyQt6.QtCore import Qt, QDir, QSize
from PyQt6.QtGui import QFileSystemModel, QPixmap, QMovie, QIcon, QFont
from Core.workers import AnalysisWorker, SameLocationWorker
from Windows.crop_window import CropWindow
from Windows.location_window import SameLocationWindow
from Windows.graph_window import LinkAnalysisWindow
from Widgets.heatmap_widget import TemporalHeatmapWidget
from Dialogs.peek_dialog import TelemetryPeekDialog
from Dialogs.search_cdr_result_dialog import SearchCdrResultDialog 
from Dialogs.timeline_dialog import TimelinePickerDialog
from Utils.pdf_report_writer import compile_case_pdf_report
import Core.index as index 
from datetime import datetime
import json
if sys.platform == "win32":
    import ctypes
    try:
        # Assign a distinct workstation identifier string to split the thread away from generic python.exe grouping
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ForensicSuite.CDRAnalyzer.Desktop.v1")
    except Exception as e:
        print(f"Taskbar grouping override failed: {e}")


# =========================================================================
# ⏳ SKYPE-STYLE FORENSIC LOADING OVERLAY WITH LIGHT/DARK TRANS-MASKS
# =========================================================================
class ForensicLoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 1️⃣ Outer overlay covering the whole screen (Lighter translucent tint layer)
        self.setStyleSheet("background-color: rgba(240, 246, 252, 0.12);")
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # Base Master Layout to hold the centered dynamic card
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 2️⃣ Inner Center Panel (Semi-transparent dark structural background card)
        self.central_card = QFrame()
        self.central_card.setFixedSize(480, 280)
        self.central_card.setStyleSheet("""
            QFrame {
                background-color: rgba(13, 17, 23, 0.88);
                border: 1px solid #30363d;
                border-radius: 12px;
            }
        """)
        
        card_layout = QVBoxLayout(self.central_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(18)
        card_layout.setContentsMargins(30, 30, 30, 30)
        
        # Center Branding Container (Skype Style)
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setStyleSheet("background: transparent; border: none;")
        
        # Safe fallback checking for local logo.png array ingestion
        if os.path.exists("logo.png"):
            pixmap = QPixmap("logo.png")
            scaled_pixmap = pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_logo.setPixmap(scaled_pixmap)
        else:
            self.lbl_logo.setText("📡")
            self.lbl_logo.setStyleSheet("font-size: 55px; background: transparent; border: none;")
            
        card_layout.addWidget(self.lbl_logo)
        
        # Status Label Description
        self.lbl_status = QLabel("Initializing Forensic Subsystem Vectors...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("""
            QLabel {
                color: #f0f6fc; 
                font-size: 14px; 
                font-weight: bold; 
                font-family: 'Segoe UI', Arial;
                background: transparent;
                border: none;
            }
        """)
        card_layout.addWidget(self.lbl_status)
        
        # Sleek Processing Bar Line
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(320)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 0) # Indeterminate loading animation pulse
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                background-color: #21262d; 
                border: none; 
                border-radius: 3px; 
            } 
            QProgressBar::chunk { 
                background-color: #58a6ff; 
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.progress_bar)
        
        # Append nested central card container into full-window screen mask
        master_layout.addWidget(self.central_card)
        
        # Hide widget by default upon system init layout staging
        self.setVisible(False)

    def trigger_loading(self, message):
        self.lbl_status.setText(message)
        if self.parentWidget():
            self.resize(self.parentWidget().size())
        self.setVisible(True)
        self.raise_()
        QApplication.processEvents()

    def dismiss_loading(self):
        self.setVisible(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline CDR Forensic Suite — Workstation Deck")
        self.resize(1450, 920)

        if os.path.exists("logo.png"):
            self.setWindowIcon(QIcon("logo.png"))
        else:
            # Fallback pathing resolution handle if working through compiled application states
            try:
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, "logo.png")
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
            except AttributeError:
                pass # Dynamic fallback if asset is physically omitted
        
        self.active_case_dir = None
        self.selected_files = []
        self.preview_rows = []
        self.last_graph_data = None
        self.last_same_loc_data = None
        self.last_spatial_roadmap = None  
        self.raw_summary_html = "" 
        self.alias_database = {}
        
        self.setStyleSheet(MAIN_DECK_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        self.central_deck_container = QWidget()
        self.setCentralWidget(self.central_deck_container)
        
        outer_layout = QVBoxLayout(self.central_deck_container)
        outer_layout.setContentsMargins(0,0,0,0)

        master_splitter = QSplitter(Qt.Orientation.Horizontal)
        master_splitter.setStyleSheet("QSplitter::handle { background-color: #30363d; width: 2px; }")

        # =========================================================================
        # 📂 LEFT SIDEBAR PANEL: DIRECTORY SYSTEM TREE + ALIAS LOOKUPS
        # =========================================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 15, 10, 15)
        left_layout.setSpacing(12)

        self.lbl_case_name = QLabel("📁 Workspace: <i>Unassigned Directory Folder</i>")
        self.lbl_case_name.setStyleSheet("color: #ffb86c; font-size: 12px; font-weight: bold;")
        left_layout.addWidget(self.lbl_case_name)

        self.btn_open_workspace = QPushButton("📂 Open Case Folder Workspace")
        self.btn_open_workspace.setStyleSheet("background-color: #1f6feb; color: white; border: none;")
        self.btn_open_workspace.clicked.connect(self.select_case_workspace)
        left_layout.addWidget(self.btn_open_workspace)

        left_layout.addWidget(QLabel("📂 Workspace Files Directory"))
        self.file_tree_view = QTreeView()
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setReadOnly(False)
        self.file_tree_view.setModel(self.file_system_model)
        self.file_tree_view.setStyleSheet("QTreeView { background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; border-radius: 4px; }")
        
        self.file_tree_view.setColumnHidden(1, True)
        self.file_tree_view.setColumnHidden(2, True)
        self.file_tree_view.setColumnHidden(3, True)
        self.file_tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.file_tree_view, 2)

        # ⚙️ INLINE ASYNC BACKGROUND STATUS BAR
        self.background_status_box = QFrame()
        self.background_status_box.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 8px;")
        self.background_status_box.setVisible(False)
        bs_layout = QVBoxLayout(self.background_status_box)
        self.lbl_background_task = QLabel("🔄 Background Processing Thread Active...")
        self.lbl_background_task.setStyleSheet("color: #58a6ff; font-size: 11px; font-weight: bold;")
        self.bg_progress_bar = QProgressBar()
        self.bg_progress_bar.setFixedHeight(4)
        self.bg_progress_bar.setTextVisible(False)
        self.bg_progress_bar.setStyleSheet("QProgressBar { background-color: #21262d; border: none; } QProgressBar::chunk { background-color: #8a63d2; }")
        bs_layout.addWidget(self.lbl_background_task)
        bs_layout.addWidget(self.bg_progress_bar)
        left_layout.addWidget(self.background_status_box)

        alias_title = QLabel("🛡️ Target Identity Aliases Profile")
        alias_title.setObjectName("SectionHeader")
        left_layout.addWidget(alias_title)

        self.form_frame = QFrame()
        self.form_frame.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 4px;")
        self.form_frame.setEnabled(False)
        form_layout = QVBoxLayout(self.form_frame)
        
        self.input_alias_num = QLineEdit()
        self.input_alias_num.setPlaceholderText("Phone Number Identifier")
        self.input_alias_name = QLineEdit()
        self.input_alias_name.setPlaceholderText("Suspect Name / Label Alias")
        self.btn_add_alias = QPushButton("➕ Register Profile")
        self.btn_add_alias.setObjectName("BtnAddAlias")
        self.btn_add_alias.clicked.connect(self.register_alias_profile)

        form_layout.addWidget(self.input_alias_num)
        form_layout.addWidget(self.input_alias_name)
        form_layout.addWidget(self.btn_add_alias)
        left_layout.addWidget(self.form_frame)

        self.alias_table = QTableWidget(0, 2)
        self.alias_table.setHorizontalHeaderLabels(["Target Number", "Assigned Alias"])
        self.alias_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.alias_table, 1)

        self.btn_save_all_pdf = QPushButton("📑 Compile & Export All to PDF Case Brief")
        self.btn_save_all_pdf.setObjectName("BtnSaveAllPdf")
        self.btn_save_all_pdf.setEnabled(False)  
        self.btn_save_all_pdf.setMinimumHeight(40)
        self.btn_save_all_pdf.clicked.connect(self.trigger_master_pdf_generation)
        left_layout.addWidget(self.btn_save_all_pdf)
        
        master_splitter.addWidget(left_widget)

        # =========================================================================
        # ⚙️ RIGHT PANEL: CORE OPERATIONAL WORKSPACE SCREEN
        # =========================================================================
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        right_container = QWidget()
        layout = QVBoxLayout(right_container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        hdr_box = QHBoxLayout()
        title_lbl = QLabel("📡 Operational Diagnostic Dashboard")
        title_lbl.setObjectName("MainHeading")
        hdr_box.addWidget(title_lbl)
        hdr_box.addStretch()
        
        self.btn_launch_crop = QPushButton("✂️ Data Cropper Tool")
        self.btn_launch_crop.clicked.connect(self.open_cropper)
        hdr_box.addWidget(self.btn_launch_crop)
        layout.addLayout(hdr_box)

        search_panel = QFrame()
        search_panel.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px;")
        search_layout = QVBoxLayout(search_panel)
        search_lbl = QLabel("🔎 Cross-File Telemetry Deep Search")
        search_lbl.setObjectName("SectionHeader")
        search_layout.addWidget(search_lbl)
        
        search_bar_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Enter tracking tokens (IMSI, IMEI, base coordinates, suspect digits)...")
        self.btn_search = QPushButton("🔍 Search Matrix")
        self.btn_search.setObjectName("BtnSearch")
        self.btn_search.clicked.connect(self.execute_cdr_search)
        search_bar_layout.addWidget(self.input_search, 4)
        search_bar_layout.addWidget(self.btn_search, 1)
        search_layout.addLayout(search_bar_layout)
        layout.addWidget(search_panel)

        panel = QFrame()
        panel.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 8px;")
        p_layout = QVBoxLayout(panel)
        f_row = QHBoxLayout()
        self.btn_select = QPushButton("📁 Stage CDR Source Vectors (.xlsx)")
        self.btn_select.clicked.connect(self.select_files)
        self.lbl_status = QLabel("Staging clean database.")
        self.lbl_status.setStyleSheet("color: #8b949e; font-style: italic;")
        f_row.addWidget(self.btn_select, 1)
        f_row.addWidget(self.lbl_status, 2)
        p_layout.addLayout(f_row)

        self.input_loc = QLineEdit()
        self.input_loc.setPlaceholderText("Filter spatial parameters keyword (e.g. Tower address, Base Sector)...")
        p_layout.addWidget(self.input_loc)
        layout.addWidget(panel)

        cmd_row = QHBoxLayout()
        self.btn_process = QPushButton("🚀 Run Intelligence Analysis")
        self.btn_process.setObjectName("ActionProcess")
        self.btn_process.clicked.connect(self.start_analysis)
        
        self.btn_same_loc = QPushButton("📍 Spatial Cross-Over Matrix")
        self.btn_same_loc.setEnabled(False)
        self.btn_same_loc.clicked.connect(self.view_same_location)
        
        self.btn_refresh = QPushButton("🔄 Reset App")
        self.btn_refresh.setObjectName("BtnRefresh")
        self.btn_refresh.clicked.connect(self.trigger_dashboard_refresh)
        
        cmd_row.addWidget(self.btn_process, 2)
        cmd_row.addWidget(self.btn_same_loc, 2)
        cmd_row.addWidget(self.btn_refresh, 1)
        layout.addLayout(cmd_row)

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setVisible(False)
        layout.addWidget(self.main_progress_bar)

        summary_frame = QFrame()
        summary_frame.setStyleSheet("border: none; padding: 0px;")
        sf_layout = QVBoxLayout(summary_frame)
        sf_layout.addWidget(QLabel("<b>🎯 Intelligence Output Summary Log</b>"))
        
        header_actions_row = QHBoxLayout()
        header_actions_row.addWidget(QLabel("Telemetry Data Stream Metrics:"))
        header_actions_row.addStretch()
        self.btn_export_summary = QPushButton("💾 Export Summary Page Separately")
        self.btn_export_summary.setVisible(False)
        self.btn_export_summary.clicked.connect(self.export_summary_content_separately)
        header_actions_row.addWidget(self.btn_export_summary)
        sf_layout.addLayout(header_actions_row)
        
        self.terminal = QTextBrowser()
        self.terminal.setMinimumHeight(220)
        self.terminal.setPlaceholderText("Intel diagnostics output matrix ready...")
        sf_layout.addWidget(self.terminal)
        layout.addWidget(summary_frame)

        self.heatmap_box = QFrame()
        self.heatmap_box.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px;")
        self.heatmap_layout = QVBoxLayout(self.heatmap_box)
        self.heatmap_box.setVisible(False)
        layout.addWidget(self.heatmap_box)

        self.badge_hw = QLabel()
        self.badge_hw.setObjectName("BadgeAlert")
        self.badge_hw.setVisible(False)
        layout.addWidget(self.badge_hw)

        self.badge_time = QLabel()
        self.badge_time.setObjectName("BadgeInfo")
        self.badge_time.setVisible(False)
        layout.addWidget(self.badge_time)

        # =========================================================================
        # 📊 MULTI-ACTION TOOL BELT BUTTONS
        # =========================================================================
        bottom_row = QHBoxLayout()
        self.btn_peek = QPushButton("👁️ Peek Live Raw Data Split Array")
        self.btn_peek.clicked.connect(self.open_peek_dialog)
        self.btn_peek.setVisible(False)

        self.btn_stay_points = QPushButton("📍 Stay Points Roadmap")
        self.btn_stay_points.setStyleSheet("background-color: #8a63d2; color: white; border: none; font-weight: bold;")
        self.btn_stay_points.clicked.connect(self.open_chronological_spatial_roadmap)
        self.btn_stay_points.setVisible(False)
        
        self.btn_graph = QPushButton("🔗 Launch 3D Topology Visualization Engine")
        self.btn_graph.setStyleSheet("background-color: #238636; color: white; border: none;")
        self.btn_graph.clicked.connect(self.open_link_graph)
        self.btn_graph.setVisible(False)
        
        bottom_row.addWidget(self.btn_peek)
        bottom_row.addWidget(self.btn_stay_points)
        bottom_row.addWidget(self.btn_graph)
        layout.addLayout(bottom_row)

        right_scroll.setWidget(right_container)
        master_splitter.addWidget(right_scroll)
        master_splitter.setSizes([340, 1010])
        
        outer_layout.addWidget(master_splitter)

        # 💡 INSTANTIATE AND EMBED THE FULL-WINDOW SKYPE SYSTEM OVERLAY CONTAINER
        self.loading_overlay = ForensicLoadingOverlay(self.central_deck_container)

    def resizeEvent(self, event):
        """Ensures that if the user expands or resizes the workstation window layout, the dark loading overlay expands to block out inputs perfectly."""
        super().resizeEvent(event)
        if self.loading_overlay.isVisible():
            self.loading_overlay.resize(self.central_deck_container.size())

    # =========================================================================
    # ⚙️ CONTROLLER LOGIC HUB & PROFILE PARSERS
    # =========================================================================
    def select_files(self):
        start_path = self.active_case_dir if self.active_case_dir else ""
        files, _ = QFileDialog.getOpenFileNames(self, "Open Worksheets", start_path, "Excel Data Sheets (*.xlsx)")
        if files:
            self.selected_files = files
            self.lbl_status.setText(f"Staged {len(files)} target documents.")
            self.lbl_status.setStyleSheet("color: #58a6ff; font-weight: bold;")

    def start_analysis(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Staging Warning", "Please select target source data layers first.")
            return

        start_ts, uq_end_ts = None, None
        reply = QMessageBox.question(
            self, 'Timeline Analysis Filter', 'Would you like to process analysis for a particular timeline boundary range constraint?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            dialog = TimelinePickerDialog(self)
            if dialog.exec() == TimelinePickerDialog.DialogCode.Accepted:
                start_ts = dialog.start_timestamp
                uq_end_ts = dialog.end_timestamp
            else: return

        chosen_output_dir = self.active_case_dir if self.active_case_dir else QFileDialog.getExistingDirectory(self, "Select Directory to Save Intelligence Package Report")
        if not chosen_output_dir: return

        # 🚫 REMOVED: Full-screen loading overlay trigger from here to rely entirely on self.main_progress_bar

        self.main_progress_bar.setRange(0, 0)
        self.main_progress_bar.setVisible(True)
        self.terminal.setText("Processing primary data partitions...")

        self.worker = AnalysisWorker(self.selected_files, self.input_loc.text(), chosen_output_dir, start_ts, uq_end_ts)
        self.worker.finished.connect(self.analysis_concluded)
        self.worker.start()

    def apply_registered_aliases_to_string(self, text_content):
        modified_string = text_content
        for target_number, allocated_alias in self.alias_database.items():
            modified_string = modified_string.replace(target_number, f"📌 {allocated_alias} [{target_number}]")
        return modified_string

    def analysis_concluded(self, result):
        self.main_progress_bar.setVisible(False)
        
        if result["status"] == "success":
            metrics = result["metrics"]
            self.preview_rows = metrics.get("preview_rows", [])
            self.last_graph_data = metrics["graph_data"]

            raw_summary = f"""
            <p><b>Target Intercepts Base Profiles (A-Parties):</b><br/><span style='color: #ff79c6;'>{metrics['a_parties']}</span></p>
            <p><b>Identified Night Stays Base Coordinates:</b><br/>{metrics['night_stays']}</p>
            <p><b>Identified Overlapping Target Cross-Links (Common B):</b><br/>{metrics['common_b_parties']}</p>
            """
            self.raw_summary_html = raw_summary 
            
            self.terminal.setHtml(self.apply_registered_aliases_to_string(raw_summary))
            self.badge_hw.setText(self.apply_registered_aliases_to_string(f"⚠️ HARDWARE THREAT VECTOR DETECTED:\n• {metrics['imei_swappers']}\n• {metrics['multi_sim']}"))
            self.badge_hw.setVisible(True)
            self.badge_time.setText(f"🕒 CHRONOLOGICAL PATTERNS:\n• {metrics['night_routine']}")
            self.badge_time.setVisible(True)

            while self.heatmap_layout.count():
                item = self.heatmap_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()

            hourly_data = metrics.get("hourly_activity", {})
            if hourly_data:
                self.heatmap_layout.addWidget(QLabel("<b>🚨 Chronological Transmission Density Logs</b>"))
                for target_ap, distribution in hourly_data.items():
                    display_header = f"{self.alias_database[target_ap]} [{target_ap}]" if target_ap in self.alias_database else target_ap
                    widget = TemporalHeatmapWidget(display_header, distribution)
                    self.heatmap_layout.addWidget(widget)
                self.heatmap_box.setVisible(True)

            self.btn_peek.setVisible(True)
            self.btn_stay_points.setVisible(True)
            self.btn_graph.setVisible(True)
            self.btn_export_summary.setVisible(True)
            
            self.start_background_roadmap_precompute(metrics.get("spatial_roadmap", []))
            self.start_background_movement_analysis()
        else:
            self.terminal.setText(f"Engine Fault: {result['message']}")
            # 🚫 REMOVED: loading_overlay.dismiss_loading() reference


    def start_background_roadmap_precompute(self, preloaded_roadmap):
        if preloaded_roadmap:
            self.last_spatial_roadmap = preloaded_roadmap
            self.background_status_box.setVisible(True)
            self.bg_progress_bar.setValue(100)
            self.lbl_background_task.setText("📍 Roadmap Pre-compute: 100% (Cached Route Loaded.)")
        else:
            self.last_spatial_roadmap = []
            self.background_status_box.setVisible(False)

    def start_background_movement_analysis(self):
        self.loc_worker = SameLocationWorker(self.selected_files)
        self.loc_worker.finished.connect(self.same_location_concluded)
        self.loc_worker.start()

    def same_location_concluded(self, result):
        """Callback handler that catches co-location background thread milestones."""
        # 1. Clear the dashboard loader overlay mask cleanly
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()
            
        if result.get("status") == "success":
            # 2. Keep standard cache states for PDF Ledger Generation
            self.last_same_loc_data = result.get("data", "[]")
            self.btn_same_loc.setEnabled(True)
            self.btn_save_all_pdf.setEnabled(True)
            
            # 3. Open the upgraded interactive window, passing files down for internal filtering
            self.loc_window = SameLocationWindow(
                raw_json_str=self.last_same_loc_data,
                file_paths=self.selected_files,
                alias_database=self.alias_database
            )
            self.loc_window.show()
        else:
            self.btn_same_loc.setEnabled(True)
            QMessageBox.critical(self, "Analysis Failure", result.get("message", "Unknown computational error."))
        # 🚫 REMOVED: loading_overlay.dismiss_loading() reference from primary background task chain

    def select_case_workspace(self):
        chosen_dir = QFileDialog.getExistingDirectory(self, "Open Case Workspace Folder")
        if not chosen_dir: return
            
        self.active_case_dir = chosen_dir
        self.lbl_case_name.setText(f"📁 Workspace: {os.path.basename(chosen_dir)}")
        self.form_frame.setEnabled(True)
        
        self.file_system_model.setRootPath(chosen_dir)
        self.file_tree_view.setRootIndex(self.file_system_model.index(chosen_dir))
        
        self.alias_database.clear()
        config_path = os.path.join(self.active_case_dir, ".cdr_workspace.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.alias_database = json.load(f)
            except Exception as e: print(f"Failed to read settings: {e}")
                
        self.refresh_alias_table_display()

    def save_workspace_aliases_to_disk(self):
        if not self.active_case_dir: return
        config_path = os.path.join(self.active_case_dir, ".cdr_workspace.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.alias_database, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"Failed to save profile: {e}")

    def register_alias_profile(self):
        number = self.input_alias_num.text().strip()
        alias = self.input_alias_name.text().strip()
        if not number or not alias: return
        self.alias_database[number] = alias
        self.refresh_alias_table_display()
        self.save_workspace_aliases_to_disk()
        self.input_alias_num.clear()
        self.input_alias_name.clear()

    def refresh_alias_table_display(self):
        self.alias_table.setRowCount(len(self.alias_database))
        for row_idx, (num, name) in enumerate(self.alias_database.items()):
            self.alias_table.setItem(row_idx, 0, QTableWidgetItem(num))
            self.alias_table.setItem(row_idx, 1, QTableWidgetItem(name))

    def trigger_master_pdf_generation(self):
        start_path = os.path.join(self.active_case_dir, "Comprehensive_Intelligence_Brief.pdf") if self.active_case_dir else "Comprehensive_Intelligence_Brief.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Unified PDF Intelligence Dossier", start_path, "PDF Documents (*.pdf)")
        if not file_path: return
            
        # ⏳ Fire Skype Loading Overlay for PDF Compiler Engine
        self.loading_overlay.trigger_loading("Assembling Intelligence Dossier into A4 PDF Formats...")

        case_title = os.path.basename(self.active_case_dir) if self.active_case_dir else "Standalone Investigation"
        loc_text = self.input_loc.text().strip()
        loc_meta_val = loc_text if loc_text else "All Sectors / Unfiltered Data Stream"
        
        timeline_meta_val = "All Time Log Volumes (Full)"
        if hasattr(self, 'worker') and self.worker:
            if self.worker.start_ts or self.worker.end_ts:
                timeline_meta_val = f"From: {self.worker.start_ts or 'Start'} To: {self.worker.end_ts or 'End'}"

        clean_cdr_filenames = [os.path.basename(p) for p in self.selected_files]
        aliased_summary = self.apply_registered_aliases_to_string(self.raw_summary_html)
        
        if self.badge_hw.isVisible():
            aliased_summary += f"<div class='badge-alert'>{self.badge_hw.text().replace('\\n','<br/>')}</div>"
        if self.badge_time.isVisible():
            aliased_summary += f"<div class='badge-info'>{self.badge_time.text().replace('\\n','<br/>')}</div>"

        pdf_preview_rows = []
        for r in self.preview_rows:
            rc = r.copy()
            if r.get("ap") in self.alias_database: rc["ap"] = f"{self.alias_database[r['ap']]} [{r['ap']}]"
            if r.get("bp") in self.alias_database: rc["bp"] = f"{self.alias_database[r['bp']]} [{r['bp']}]"
            pdf_preview_rows.append(rc)

        res = compile_case_pdf_report(
            file_path, case_title, aliased_summary, pdf_preview_rows, 
            self.last_same_loc_data, self.last_graph_data,
            alias_database=self.alias_database,
            location_request=loc_meta_val,
            timeline_analysis=timeline_meta_val,
            cdr_names=clean_cdr_filenames
        )
        
        # 🔓 Dismiss loading screen when disk generation loop completes
        self.loading_overlay.dismiss_loading()

        if res["status"] == "success":
            QMessageBox.information(self, "Export Success", f"Unified Forensic Intelligence Brief saved:\n{file_path}")
        else:
            QMessageBox.critical(self, "Export Failure", res["message"])

    def trigger_dashboard_refresh(self):
        self.selected_files.clear()
        self.preview_rows.clear()
        self.last_graph_data = None
        self.last_same_loc_data = None
        self.last_spatial_roadmap = None  
        self.raw_summary_html = ""
        
        self.lbl_status.setText("Staging array cleared.")
        self.lbl_status.setStyleSheet("color: #8b949e; font-style: italic;")
        self.input_loc.clear()
        self.input_search.clear()
        
        self.terminal.clear()
        self.terminal.setPlaceholderText("Intel diagnostics output matrix ready...")
        
        self.badge_hw.setVisible(False)
        self.badge_time.setVisible(False)
        self.btn_peek.setVisible(False)
        self.btn_stay_points.setVisible(False)
        self.btn_graph.setVisible(False)
        self.btn_export_summary.setVisible(False)
        self.btn_same_loc.setEnabled(False)
        self.btn_save_all_pdf.setEnabled(False)
        self.background_status_box.setVisible(False)
        
        while self.heatmap_layout.count():
            item = self.heatmap_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.heatmap_box.setVisible(False)
        QMessageBox.information(self, "System Reset", "Forensic layout cache terminal flushed cleanly.")

    def export_summary_content_separately(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Dashboard Summary", "Summary_Metrics.html", "HTML Files (*.html)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.terminal.toHtml())
                QMessageBox.information(self, "Success", "Summary report webpage saved successfully.")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def execute_cdr_search(self):
        query = self.input_search.text().strip()
        if not query or not self.selected_files: return
        res = index.search_cdr_data(self.selected_files, query)
        if res["status"] == "success":
            dialog = SearchCdrResultDialog(self, self.apply_registered_aliases_to_string(res["summary_html"]))
            dialog.exec()
            self.input_search.clear()

    def open_cropper(self):
        self.crop_win = CropWindow()
        self.crop_win.show()

    def open_peek_dialog(self):
        if self.preview_rows:
            mapped_rows = []
            for row in self.preview_rows:
                mapped_row = row.copy()
                if row.get("ap") in self.alias_database: mapped_row["ap"] = f"{self.alias_database[row['ap']]} [{row['ap']}]"
                if row.get("bp") in self.alias_database: mapped_row["bp"] = f"{self.alias_database[row['bp']]} [{row['bp']}]"
                mapped_rows.append(mapped_row)
            dialog = TelemetryPeekDialog(self, mapped_rows)
            dialog.exec()

    def view_same_location(self):
        if self.last_same_loc_data:
            self.loc_window = SameLocationWindow(self.last_same_loc_data, self.alias_database)
            self.loc_window.show()

    def open_link_graph(self):
        if self.last_graph_data:
            self.graph_window = LinkAnalysisWindow(self.last_graph_data, self.alias_database)
            self.graph_window.show()

    
    def open_chronological_spatial_roadmap(self):
        if hasattr(self, 'last_spatial_roadmap') and self.last_spatial_roadmap:
            from Windows.chronological_spatial_analysis import ChronologicalSpatialAnalysisWindow
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            
            self.loading_overlay.trigger_loading("Rendering Interactive Chronological Spatial Web Canvas...")
            
            # 1️⃣ Map dynamic user aliases across tracking parameters (Keep as a FLAT array)
            aliased_roadmap = []
            for node in self.last_spatial_roadmap:
                node_copy = node.copy()
                ap_num = node_copy.get("A_Party", "")
                bp_num = node_copy.get("B_Party", "")
                loc_str = node_copy.get("Location", "")
                
                if ap_num in self.alias_database:
                    node_copy["A_Party"] = f"{self.alias_database[ap_num]} [{ap_num}]"
                if bp_num in self.alias_database:
                    node_copy["B_Party"] = f"{self.alias_database[bp_num]} [{bp_num}]"
                    
                for stored_num, assigned_name in self.alias_database.items():
                    if stored_num in loc_str:
                        loc_str = loc_str.replace(stored_num, f"📌 {assigned_name} [{stored_num}]")
                node_copy["Location"] = loc_str
                aliased_roadmap.append(node_copy)
                
            # 2️⃣ Launch display window instance
            self.spatial_roadmap_win = ChronologicalSpatialAnalysisWindow(aliased_roadmap, self.alias_database, self)
            self.spatial_roadmap_win.show()
            
            # 3️⃣ Safely find the QWebEngineView child component
            web_view_widget = self.spatial_roadmap_win.findChild(QWebEngineView)
            
            if web_view_widget:
                json_payload = json.dumps(aliased_roadmap, ensure_ascii=False)
                # Call the exact function name 'renderRoadmapData' with the flat array payload
                web_view_widget.page().loadFinished.connect(
                    lambda: web_view_widget.page().runJavaScript(f"renderRoadmapData({json_payload});")
                )
            else:
                print("⚠️ Core Alert: Could not dynamically locate WebEngine instance view panel.")
                
            self.loading_overlay.dismiss_loading()
        else:
            QMessageBox.warning(self, "Data Error", "No telemetry roadmap frames available in cache ledger.")
            
            
MAIN_DECK_STYLESHEET = """
    QMainWindow { background-color: #0d1117; }
    QLabel { color: #c9d1d9; font-size: 13px; }
    #MainHeading { color: #f0f6fc; font-size: 22px; font-weight: bold; }
    #SectionHeader { color: #58a6ff; font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    QLineEdit { background-color: #161b22; color: #f0f6fc; border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-size: 13px; }
    QLineEdit:focus { border: 1px solid #58a6ff; }
    QPushButton { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-weight: bold; font-size: 13px; }
    QPushButton:hover { background-color: #30363d; border-color: #8b949e; color: #f0f6fc; }
    #ActionProcess { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:1 #388bfd); color: white; border: none; }
    #ActionProcess:hover { background: #388bfd; }
    #BtnAddAlias { background-color: #238636; color: white; border: none; padding: 8px; }
    #BtnAddAlias:hover { background-color: #2ea44f; }
    #BtnSearch { background: #8a63d2; color: white; border: none; padding: 10px 15px; }
    #BtnSearch:hover { background: #9a73e2; }
    #BtnRefresh { background-color: #21262d; color: #f0f6fc; border: 1px solid #f06595; }
    #BtnRefresh:hover { background-color: #f06595; color: white; }
    #BtnSaveAllPdf { background-color: #8b263e; color: white; border: none; font-size: 13px; font-weight: bold; margin-top: 5px; }
    #BtnSaveAllPdf:hover { background-color: #a83251; }
    #BtnSaveAllPdf:disabled { background-color: #161b22; color: #484f58; border: 1px solid #21262d; }
    QTableWidget { background-color: #161b22; border: 1px solid #30363d; gridline-color: #21262d; color: #c9d1d9; border-radius: 6px; }
    QHeaderView::section { background-color: #21262d; color: #f0f6fc; border: 1px solid #30363d; font-weight: bold; padding: 4px; }
    #BadgeAlert { background-color: #211515; border: 1px solid #6b1d1d; border-radius: 5px; color: #ff6b6b; padding: 10px; font-size: 13px; font-weight: bold; }
    #BadgeInfo { background-color: #151b26; border: 1px solid #1f6feb; border-radius: 5px; color: #58a6ff; padding: 10px; font-size: 13px; font-weight: bold; }
    QTextBrowser { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; color: #c9d1d9; }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 🎯 FORCE GLOBAL APP ICON (This handles the Windows Taskbar slot explicitly during dev)
    if os.path.exists("logo.png"):
        app.setWindowIcon(QIcon("logo.png"))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())