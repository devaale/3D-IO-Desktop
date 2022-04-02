import pyrealsense2 as rs
from datetime import datetime
import os
from desktop_app.services.camera.data_saver import DataSaver


class DepthFrameSaver:
    DIR_NAME = os.path.dirname(os.path.abspath(__file__))
    DEPTH_FRAME_FOLDER = os.path.join(DIR_NAME, "depth_frame/")

    def __init__(self, count):
        self.__curr_count = 0
        self.__count = count
        self.__saver = rs.save_single_frameset()
        self.__data_saver = DataSaver(self.DEPTH_FRAME_FOLDER)

    def save_frame(self, frame, product_type, scan_number):
        if self.__curr_count != self.__count:
            self.__data_saver.save_raw_frame(
                frame, product_type, scan_number, datetime.now()
            )
            self.__curr_count += 1

    def save(self, frames):
        if self.__curr_count != self.__count:
            self.__saver.process(frames)
            self.__curr_count += 1
