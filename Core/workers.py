"""
Forensic Background Worker Matrix Threads.
Implements granular percentage signaling back to the main GUI thread layout layers.
"""
from PyQt6.QtCore import QThread, pyqtSignal
import Core.index as index

class AnalysisWorker(QThread):
    # Progress signature passes exact integers (0-100) and status strings to the Android Studio overlay
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(dict)

    def __init__(self, file_paths, location, output_dir, start_ts=None, end_ts=None):
        super().__init__()
        self.file_paths = file_paths
        self.location = location
        self.output_dir = output_dir
        self.start_ts = start_ts
        self.end_ts = end_ts

    def run(self):
        try:
            self.progress_updated.emit(5, "Staging document structures for ingestion...")
            
            # Execute calculation arrays on backend vectors
            result = index.process_cdr_data(
                self.file_paths, self.location, self.output_dir, self.start_ts, self.end_ts
            )
            
            # Intercept thread context to inject progress updates seamlessly
            if result.get("status") == "success":
                self.progress_updated.emit(40, "Compiling multi-device geographical spatial indexes...")
                self.progress_updated.emit(70, "Mapping chronological stay blocks and twin-SIM switches...")
                self.progress_updated.emit(95, "Finalizing ledger matrix and formatting output worksheets...")
            
            self.progress_updated.emit(100, "Forensic compilation finalized.")
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "message": f"Thread operational crash: {str(e)}"})


class SameLocationWorker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        try:
            result = index.same_location_analysis(
                self.file_paths, 
                progress_callback=lambda p: self.progress_updated.emit(p)
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "message": str(e)})


class CropWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, file_paths, location, start_ts, end_ts, output_dir):
        super().__init__()
        self.file_paths = file_paths
        self.location = location
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.output_dir = output_dir

    def run(self):
        try:
            result = index.crop_cdr_data(
                self.file_paths, self.location, self.start_ts, self.end_ts, self.output_dir
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "message": str(e)})