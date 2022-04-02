from typing import List
from .corner import Corner
from ....common.logger import logger


class Reference(object):
    def __init__(self, position: int, row_position: int, max_height: float = 0):
        self.corners = []
        self.average_height = 0

        self.position = position
        self.row_position = row_position
        self.max_height = max_height

        self.set_corners()

    def set_corners(self):
        self.corners.append(Corner([], 0))
        self.corners.append(Corner([], 1))
        self.corners.append(Corner([], 2))
        self.corners.append(Corner([], 3))

    def set_corner(self, corner: Corner, position: int):
        self.corners[position] = corner

    def accumulate_corner_average(self, points, distance_to_table, corner_index):
        self.corners[corner_index].accumulate_average_height(points, distance_to_table)

    def recalculate_corners_averages(self):
        for corner in self.corners:
            corner.recalculate_average_height()

    def append_corners_average_heights(self, corners: List[Corner]):
        self.log_self()
        for corner in self.corners:
            for other_corner in corners:
                if corner.equal(other_corner.position):
                    corner.append_average_height(other_corner.avg_height)

    # def recalculate_appended_corners_heights(self):
    #     for corner in self.corners:
    #         corner.recalculate_appended_height()

    # def sum_corners_average_heights(self, corners: List[Corner]):
    #     self.log_self()
    #     for corner in self.corners:
    #         for other_corner in corners:
    #             if corner.equal(other_corner.position):
    #                 corner.sum_average_height(other_corner.avg_height)

    def compare(self, col_pos: int, row_pos: int):
        return self.position == col_pos and self.row_position == row_pos

    def log_self(self):
        logger.info(
            "This is reference at position: "
            + str(self.position)
            + ", row pos.:"
            + str(self.row_position)
        )

    def log(self):
        logger.info(
            "This is reference at position: "
            + str(self.position)
            + ", row pos.:"
            + str(self.row_position)
        )
        for corner in self.corners:
            corner.log()
            pass
