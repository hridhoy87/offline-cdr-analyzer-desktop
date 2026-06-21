"""
Forensic Background Worker Matrix Threads.
Optimized for Real-Time Engine Callbacks and Disk-Backed Cache Routing.
"""
from PyQt6.QtCore import QThread, pyqtSignal
import Core.index as index  

class LocationGroupWorker(QThread):
    """
    Asynchronous forensic background matrix worker thread.
    Triggers chronological location grouping and routes the .cache file path to the UI.
    """
    finished = pyqtSignal(dict)

    def __init__(self, file_paths, start_ts=None, end_ts=None):
        super().__init__()
        self.file_paths = file_paths
        self.start_ts = start_ts
        self.end_ts = end_ts

    def run(self):
        try:
            # Executes calculation and returns a lightweight dictionary containing the cache_path
            result = index.group_location_by_date_by_CDR(
                file_paths=self.file_paths,
                start_ts=self.start_ts,
                end_ts=self.end_ts
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "message": f"Location worker thread failure: {str(e)}"})

class AnalysisWorker(QThread):
    """
    Primary processing thread. 
    Passes real-time progress to the UI while the engine natively writes Parquet files to disk.
    """
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
            self.progress_updated.emit(5, "Initializing forensic engine protocols...")
            
            # The engine writes master_data.parquet and returns the path inside the 'result' dictionary
            result = index.process_cdr_data(
                file_paths=self.file_paths, 
                intended_location=self.location, 
                output_dir=self.output_dir, 
                start_ts=self.start_ts, 
                end_ts=self.end_ts,
                progress_callback=self.progress_updated.emit  # Direct signal injection
            )
            
            if result.get("status") == "success":
                self.progress_updated.emit(100, "Forensic cache compilation finalized.")
                
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "message": f"Thread operational crash: {str(e)}"})


class SameLocationWorker(QThread):
    """
    Thread for concurrent location overlaps. 
    Signals the UI when the overlap_matrix.parquet cache file is fully generated and ready.
    """
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, file_paths, start_ts=None, end_ts=None):
        super().__init__()
        self.file_paths = file_paths
        self.start_ts = start_ts
        self.end_ts = end_ts

    def run(self):
        try:
            result = index.same_location_analysis(
                file_paths=self.file_paths,
                progress_callback=self.progress_updated.emit,
                start_ts=self.start_ts,
                end_ts=self.end_ts
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"status": "error", "message": str(e)})


class CropWorker(QThread):
    """
    Extracts bounded time frames or location sub-segments asynchronously directly to an output file.
    """
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