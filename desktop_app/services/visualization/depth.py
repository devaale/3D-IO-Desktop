import open3d as o3d
import cv2
import pyrealsense2 as rs
import numpy as np


class Visualizer3D(object):
    def __init__(self):
        self._source = o3d.geometry.PointCloud

        self._grid_lines = o3d.geometry.Geometry

        self._boxes_lines = o3d.geometry.Geometry

        self._visualiser = o3d.visualization.Visualizer()

        self._created = False

        self._enabled = False

    def create_window(self):
        if self._created:
            return
        self._created = True
        self._visualiser.create_window()

    def render(self, source: o3d.geometry.PointCloud):
        if source is None:
            return

        if not self._created:
            self.create_window()
            self.add_cloud(source)
            self._first_render = False
            return

        self.update_cloud(source)

    def add_cloud(self, source: o3d.geometry.PointCloud):
        self._source = source
        self._visualiser.add_geometry(self._source)

    def update_cloud(self, source: o3d.geometry.PointCloud):
        self._source.points = source.points
        self._source.colors = source.colors

        self._visualiser.update_geometry(self._source)
        self._visualiser.poll_events()
        self._visualiser.update_renderer()

    def add_boxes_lines(self, source: o3d.geometry.Geometry):
        self._boxes_lines = source

        self._visualiser.add_geometry(self._boxes_lines, reset_bounding_box=False)

    def update_boxes_lines(self, source: o3d.geometry.Geometry):
        self._visualiser.remove_geometry(self._boxes_lines, reset_bounding_box=False)

        self._boxes_lines = source

        self._visualiser.add_geometry(self._boxes_lines, reset_bounding_box=False)

    def add_grid(self, source: o3d.geometry.Geometry):
        self._grid_lines = source

        self._visualiser.add_geometry(self._grid_lines, reset_bounding_box=False)

    def update_grid(self, grid_lines: o3d.geometry.Geometry):
        self._visualiser.remove_geometry(self._grid_lines, reset_bounding_box=False)

        self._grid_lines = grid_lines

        self._visualiser.add_geometry(self._grid_lines, reset_bounding_box=False)

    def is_closed(self) -> bool:
        return not self._visualiser.poll_events()

    def destroy(self):
        if not self._created:
            return
        self._created = False
        self._visualiser.destroy_window()

    def __del__(self):
        self.destroy()

    @staticmethod
    def display_fps(start, end):
        fps = str("FPS: % 2.0f" % (1 / (end - start)))
        time = str("TIME: % .0f ms" % (1000 * (end - start)))

        img = np.zeros((150, 300, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_size = 1
        font_color = (100, 255, 0)

        cv2.putText(img, fps, (10, 40), font, font_size, font_color, 3, cv2.LINE_AA)
        cv2.putText(img, time, (10, 80), font, font_size, font_color, 3, cv2.LINE_AA)

        cv2.imshow("Functions time / FPS", img)

    @staticmethod
    def display_2d(depth_frame: rs.depth_frame, rgb_frame: rs.frame):
        colorizer = rs.colorizer()

        colorized_depth = np.asanyarray(colorizer.colorize(depth_frame).get_data())

        depth_image = np.hstack((rgb_frame.get_data(), colorized_depth))

        cv2.imshow("depth", depth_image)

        cv2.waitKey(1)
