from PyQt6.QtCore import QThread, pyqtSignal
import Core.index as index

class AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    
    def __init__(self, file_paths, location, output_dir, start_ts, end_ts):
        super().__init__()
        self.file_paths = file_paths
        self.location = location
        self.output_dir = output_dir
        self.start_ts = start_ts
        self.end_ts = end_ts

    def run(self):
        result = index.process_cdr_data(
            self.file_paths, self.location, self.output_dir, self.start_ts, self.end_ts
        )
        self.finished.emit(result)

class SameLocationWorker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        result = index.same_location_analysis(
            self.file_paths, 
            progress_callback=lambda p: self.progress_updated.emit(p)
        )
        self.finished.emit(result)

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
        result = index.crop_cdr_data(
            self.file_paths, self.location, self.start_ts, self.end_ts, self.output_dir
        )
        self.finished.emit(result)