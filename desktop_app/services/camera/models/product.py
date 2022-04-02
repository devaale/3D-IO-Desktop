import numpy as np
from desktop_app.common import utils
from typing import List
from .corner import Corner
from .reference import Reference
from .bounding_box import BoundingBox


class Product(object):
    def __init__(
        self,
        points: [],
        bounding_box: BoundingBox,
        position: int = 0,
        row_position: int = 0,
        max_height: float = 0,
    ):
        self.__points = points
        self.__bounding_box = bounding_box

        self.position = position
        self.row_position = row_position
        self.max_height = max_height

        self.correct = False
        self.corners = []

    @property
    def max_bound(self) -> BoundingBox:
        return [self.__bounding_box.max_x, self.__bounding_box.max_y, self.__bounding_box.max_z]

    @property
    def min_bound(self) -> BoundingBox:
        return [self.__bounding_box.min_x, self.__bounding_box.min_y, self.__bounding_box.min_z]
        
    def set_corners(self, ground_distance: float, size: float):
        self.set_corner(0, ground_distance, size)
        self.set_corner(1, ground_distance, size)
        self.set_corner(2, ground_distance, size)
        self.set_corner(3, ground_distance, size)

    def sum_corners_average_heights(self, corners: List[Corner]):
        for corner in self.corners:
            for other_corner in corners:
                if corner.equal(other_corner.position):
                    corner.sum_average_height(other_corner.avg_height)

    def set_corner(self, position: int, ground_distance: float, size: float):
        min_x, max_x = utils.corner_min_max_x(self.__bounding_box, position, size)
        min_y, max_y = utils.corner_min_max_y(self.__bounding_box, position, size)

        points_bounded = utils.bounded_points(self.__points, min_x, max_x, min_y, max_y)

        corner = Corner(points_bounded, position)
        corner.calculate_average_height(ground_distance)

        self.corners.append(corner)

    def compare(self, reference: Reference, threshold: float):
        avg_height_0 = self.corners[0].compare(
            reference.corners[0].avg_height, threshold
        )
        avg_height_1 = self.corners[1].compare(
            reference.corners[1].avg_height, threshold
        )
        avg_height_2 = self.corners[2].compare(
            reference.corners[2].avg_height, threshold
        )
        avg_height_3 = self.corners[3].compare(
            reference.corners[3].avg_height, threshold
        )

        self.max_height = max_difference = np.max(
            [avg_height_0, avg_height_1, avg_height_2, avg_height_3]
        )
        if any(not corner.correct for corner in self.corners):
            self.correct = False
        else:
            self.correct = True

        return max_difference

    def compare_max_height(self, other_height: float, threshold: float):
        print("MAX HEIGHT DIFFERENCE: ================== ")
        if abs(self.max_height - other_height) > threshold:
            print(
                "This is product at position: ",
                self.position,
                " -- row :",
                self.row_position,
                " INCORRECT",
            )
        else:
            print(
                "This is product at position: ",
                self.position,
                " -- row :",
                self.row_position,
                " CORRECT",
            )
        print("Difference: " + str(abs(self.max_height - other_height)))

        return abs(self.max_height - other_height)

    def get_corner_points(self):
        return self.__bounding_box.corner_points

    def say_short_hello(self):
        print(
            "This is product at position: ",
            self.position,
            " -- ",
            self.row_position,
            ", CORRECT: ",
            self.correct,
        )

    def say_hello(self):
        print(
            "This is product at position: ",
            self.position,
            " -- ",
            self.row_position,
            ", CORRECT: ",
            self.correct,
        )
        for corner in self.corners:
            corner.log()
