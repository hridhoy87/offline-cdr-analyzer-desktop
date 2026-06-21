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
        self._engine = QWebEngineView()
        self._save_path = ""
        self._temp_file = ""
        
        self._timeout_timer = QTimer()
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)
        
        self._engine.loadFinished.connect(self._on_html_loaded)
        self._engine.page().pdfPrintingFinished.connect(self._on_pdf_printed)

    def export_html_to_pdf(self, html_content: str, save_path: str):
        self._save_path = save_path
        self._timeout_timer.start(45000) 

        # 💡 BYPASS IPC LIMITS: Write HTML to a temp file and load it as a Local URL
        self._temp_file = os.path.join(tempfile.gettempdir(), f"cdr_report_temp_{id(self)}.html")
        try:
            with open(self._temp_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            self._engine.setUrl(QUrl.fromLocalFile(self._temp_file))
        except Exception as e:
            self.export_finished.emit(False, f"Failed to mount temporary storage for Chromium: {str(e)}")

    def _on_timeout(self):
        self._engine.stop()
        self._cleanup_temp_file()
        self.export_finished.emit(False, "Export Error: Chromium engine timed out while processing massive HTML.")
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, "Export Error", "The PDF rendering engine timed out. The dataset may be too massive for a single PDF.")

    def _on_html_loaded(self, success: bool):
        self._timeout_timer.stop() 
        
        if not success:
            self._cleanup_temp_file()
            self.export_finished.emit(False, "Chromium engine failed to mount the DOM structure.")
            return

        margins = QMarginsF(0.4, 0.4, 0.4, 0.4)
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            margins,
            QPageLayout.Unit.Inch
        )

        QTimer.singleShot(1000, lambda: self._engine.page().printToPdf(self._save_path, layout))

    def _on_pdf_printed(self, file_path: str, success: bool):
        self._cleanup_temp_file()
        
        if success:
            self.export_finished.emit(True, file_path)
            if self.parent_widget:
                QMessageBox.information(self.parent_widget, "Export Finalized", f"Intelligence Brief saved successfully:\n{os.path.normpath(file_path)}")
        else:
            self.export_finished.emit(False, "Failed to write PDF to disk. File may be open in another program.")

    def _cleanup_temp_file(self):
        try:
            if os.path.exists(self._temp_file):
                os.remove(self._temp_file)
        except:
            pass