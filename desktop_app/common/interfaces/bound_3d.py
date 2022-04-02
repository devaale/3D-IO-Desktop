from typing import List
import open3d as o3d
from abc import ABC, abstractmethod


class Bound3D(ABC):
    @property
    @abstractmethod
    def points(self) -> List[List[float]]:
        pass

    @points.setter
    @abstractmethod
    def points(self, value) -> None:
        pass

    @property
    @abstractmethod
    def box(self) -> o3d.geometry.PointCloud:
        pass

    @box.setter
    @abstractmethod
    def box(self, value) -> None:
        pass
    
    @property
    @abstractmethod
    def colors(self):
        pass

    @colors.setter
    @abstractmethod
    def colors(self, value):
        pass
    
    @abstractmethod
    def set_random_color(self):
        pass
