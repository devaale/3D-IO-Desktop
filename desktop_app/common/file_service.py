
from datetime import datetime
from desktop_app.common.logger import logger
from dataclasses import dataclass, field
import os, shutil
from desktop_app.common.periodic_timed_service import PeriodicTimedService
from desktop_app.common import utils

@dataclass
class FileService:
    first_run: bool = True
    directories: list = field(default=list, init=True)
    exlude_files: str = field(default=list, init=True)
    timed_service: PeriodicTimedService = None

    def __init_data(self, delay_days: int):
        delay_sec = utils.days_to_seconds(delay_days)
        self.directories = []
        self.exlude_files = ["__init__.py"]

        if not self.timed_service is None:
            return
        self.timed_service = PeriodicTimedService(self.clean_directories, delay_sec)
        self.timed_service.daemon = True

    def start(self, delay_days: int):
        logger.info("[File Service] Started, cleaning directories every: " + str(delay_days) + " day / days.")
        self.__init_data(delay_days)
        self.timed_service.start()

    def stop(self):
        if not self.timed_service is None:
            self.timed_service.stop()
    
    def clean_directories(self):
        if self.first_run:
            return

        logger.info("[File Service] " + str(datetime.now()) + ", Cleaning directories")

        directories = self.find_required_dirs()

        for directory in directories:
            self.delete_files(directory)

    def find_required_dirs(self):
        directories = []

        for directory, _, _ in os.walk('.'):
            if self.is_required(directory):
                directories.append(directory)
        
        return directories
        

    def is_required(self, directory: str):
        dir_names = ["clustered", "raw", "clustered_modified", "original", "processed", "result"]
        for name in dir_names:
            if name in directory:
                return True
        
        return False

    def is_excluded(self, file: str):
        for excluded in self.exlude_files:
            if excluded in file:
                return True
        
        return False

    def delete_files(self, directory: str):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if self.is_excluded(file_path):
                    logger.info("[File Service] File is excluded from deletion: " + str(file_path))
                    continue
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                
                print("File: ", file_path)
            except Exception as e:
                logger.error('[File Service] Failed to delete: ' + str(file_path) + ', Reason: ' + str(e))