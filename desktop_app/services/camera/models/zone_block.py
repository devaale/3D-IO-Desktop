import open3d as o3d
import numpy as np
from random import uniform
from dataclasses import dataclass, field
from desktop_app.common.interfaces.bound_3d import Bound3D
from desktop_app.common.logger import logger

@dataclass
class ZoneBlock(Bound3D):
    row: int
    col: int
    avg_depth: float
    __box: o3d.geometry.OrientedBoundingBox = None
    __points: list = field(default_factory=list)
    __colors: list = field(default_factory=list)
    
    @property
    def points(self):
        return self.__points
    
    @points.setter
    def points(self, points):
        self.__points = points.copy()

    @property
    def colors(self):
        return self.__colors

    @colors.setter
    def colors(self, value):
        if len(self.__points) == 0:
            logger.warning("[Zone Block] [" + str(self.row) + ", " + str(self.col) + "] Unable to set color. No points")
            return
        self.__colors = np.zeros((len(np.asarray(self.__points)), 3))
        self.__colors[:, 0] = value

    def set_random_color(self):
        if len(self.__points) == 0:
            logger.warning("[Zone Block] [" + str(self.row) + ", " + str(self.col) + "] Unable to set color. No points")
            return
        self.__colors = np.zeros((len(np.asarray(self.__points)), 3))
        self.__colors[:, 0] = uniform(0, 1)
        self.__colors[:, 1] = uniform(0, 1)

    @property
    def box(self) -> o3d.geometry.OrientedBoundingBox:
        return self.__box
    
    @box.setter
    def box(self, value: o3d.geometry.OrientedBoundingBox):
        self.__box = value