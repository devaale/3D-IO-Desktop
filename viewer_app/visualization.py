import open3d as o3d
import cv2
import pyrealsense2 as rs
import numpy as np


class Visualization(object):
    def __init__(self):
        self.__source = o3d.geometry.PointCloud

        self.__grid_lines = o3d.geometry.Geometry

        self.__boxes_lines = o3d.geometry.Geometry

        self.__visualiser = o3d.visualization.Visualizer()

        self.__created = False
    
    def create_window(self):
        if self.__created:
            return
        self.__created = True
        self.__visualiser.create_window()

    def add_cloud(self, source: o3d.geometry.PointCloud):
        self.__source = source
        self.__visualiser.add_geometry(self.__source)

    def update_cloud(self, source: o3d.geometry.PointCloud):
        self.__source.points = source.points
        self.__source.colors = source.colors

        self.__visualiser.update_geometry(self.__source)
        self.__visualiser.poll_events()
        self.__visualiser.update_renderer()

    def add_boxes_lines(self, source: o3d.geometry.Geometry):
        self.__boxes_lines = source

        self.__visualiser.add_geometry(self.__boxes_lines, reset_bounding_box=False)

    def update_boxes_lines(self, source: o3d.geometry.Geometry):
        self.__visualiser.remove_geometry(self.__boxes_lines, reset_bounding_box=False)

        self.__boxes_lines = source

        self.__visualiser.add_geometry(self.__boxes_lines, reset_bounding_box=False)

    def add_grid(self, source: o3d.geometry.Geometry):
        self.__grid_lines = source

        self.__visualiser.add_geometry(self.__grid_lines, reset_bounding_box=False)

    def update_grid(self, grid_lines: o3d.geometry.Geometry):
        self.__visualiser.remove_geometry(self.__grid_lines, reset_bounding_box=False)

        self.__grid_lines = grid_lines

        self.__visualiser.add_geometry(self.__grid_lines, reset_bounding_box=False)

    def is_closed(self) -> bool:
        return not self.__visualiser.poll_events()

    def destroy(self):
        if not self.__created:
            return
        self.__created = False
        self.__visualiser.destroy_window()

    def __del__(self):
        self.destroy()

    @staticmethod
    def display_fps(start, end):
        fps = str('FPS: % 2.0f' % (1 / (end - start)))
        time = str('TIME: % .0f ms' % (1000 * (end - start)))

        img = np.zeros((150, 300, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_size = 1
        font_color = (100, 255, 0)

        cv2.putText(img, fps, (10, 40), font, font_size, font_color, 3, cv2.LINE_AA)
        cv2.putText(img, time, (10, 80), font, font_size, font_color, 3, cv2.LINE_AA)

        cv2.imshow('Functions time / FPS', img)

    @staticmethod
    def display_2d(depth_frame: rs.depth_frame, rgb_frame: rs.frame):
        colorizer = rs.colorizer()

        colorized_depth = np.asanyarray(colorizer.colorize(depth_frame).get_data())

        depth_image = np.hstack((rgb_frame.get_data(), colorized_depth))

        cv2.imshow("depth", depth_image)

        cv2.waitKey(1)
