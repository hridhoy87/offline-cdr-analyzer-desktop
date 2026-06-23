import os
import tempfile
from PyQt6.QtCore import QObject, pyqtSignal, QMarginsF, QTimer, QUrl
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMessageBox

class PDFExportManager(QObject):
    export_finished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # FIX: Bind WebEngine to a parent to protect it from Python Garbage Collection
        self._engine = QWebEngineView(self.parent_widget or self)
        
        self._save_path = ""
        self._temp_file = ""
        
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)
        
        self._engine.loadFinished.connect(self._on_html_loaded)
        self._engine.page().pdfPrintingFinished.connect(self._on_pdf_printed)

    def export_html_to_pdf(self, html_content: str, save_path: str):
        self._save_path = save_path
        self._timeout_timer.start(120000) # 120s timeout threshold

        self._temp_file = os.path.join(tempfile.gettempdir(), f"dossier_{id(self)}.html")
        
        # FIX: Catch permission/disk-space errors during temp write
        try:
            with open(self._temp_file, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception as e:
            self._timeout_timer.stop()
            self.export_finished.emit(False, f"File IO Exception: {str(e)}")
            return
            
        self._engine.setUrl(QUrl.fromLocalFile(self._temp_file))

    def _on_timeout(self):
        self._engine.stop()
        self._cleanup_temp_file()
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, "Export Error", "Rendering engine timed out. Dataset exceeds Chromium buffer limits.")
        self.export_finished.emit(False, "Timeout Exception")

    def _on_html_loaded(self, success: bool):
        if not success:
            self._cleanup_temp_file()
            self.export_finished.emit(False, "Failed to inject payload into WebEngine.")
            return
        
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4), 
            QPageLayout.Orientation.Portrait, 
            QMarginsF(0.5, 0.5, 0.5, 0.5), 
            QPageLayout.Unit.Inch
        )
        
        # Defer print slightly to let Chromium stabilize the DOM mapping
        QTimer.singleShot(5000, lambda: self._engine.page().printToPdf(self._save_path, layout))

    def _on_pdf_printed(self, file_path: str, success: bool):
        self._timeout_timer.stop()
        self._cleanup_temp_file()
        self.export_finished.emit(success, file_path)

    # FIX: Added the missing cleanup method to prevent the silent AttributeError crashes
    def _cleanup_temp_file(self):
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except Exception as e:
                print(f"Warning: Cached dossier cleanup deferred. {e}")