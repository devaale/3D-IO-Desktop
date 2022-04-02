from logging import log
import numpy as np
from ....common.logger import logger


class Corner(object):
    def __init__(self, points=[], position: int = 0, avg_height=0):
        self.points = points
        self.position = position

        self.count = 0
        self.avg_height = avg_height

        self.appended_heights = []

        self.colors = np.zeros((len(self.points), 3))
        self.correct = False
        # print("Corner, ", position, "has points: ", len(self.points))
        self.set_color()

    def calculate_average_height(self, distance_to_ground: float):
        if len(self.points) > 0:
            self.avg_height = distance_to_ground - np.mean(self.points, axis=0)[2]
        else:
            logger.warning(
                "No points found for average calculation, corner: " + str(self.position)
            )
            self.avg_height = 0

    def recalculate_average_height(self):
        self.avg_height = 0 if self.count == 0 else (self.avg_height / self.count)

    def accumulate_average_height(self, points, distance_to_ground: float):
        self.count += 1
        self.avg_height += distance_to_ground - np.mean(points, axis=0)[2]

    def append_average_height(self, height):
        print("Corner at position: ", self.position, " +++ Appending value: ", height)
        self.appended_heights.append(height)

    def recalculate_appended_height(self):
        if self.avg_height != 0:
            self.appended_heights.append(self.avg_height)
        print("Using values for calculation: ", self.appended_heights)
        self.avg_height = np.mean(self.appended_heights)
        self.appended_heights.clear()

    def sum_average_height(self, height):
        print("Summing value: ", height)
        self.avg_height = (
            height if self.avg_height == 0 else np.mean([self.avg_height, height])
        )
        print(
            "Height after sum, position: ",
            self.position,
            " -- HEIGHT: ",
            self.avg_height,
        )

    def compare(self, reference_height, height_threshold):
        if reference_height is None:
            logger.warning(
                "Reference corner height is None, corner: " + str(self.position)
            )
            self.set_incorrect()
        elif abs(self.avg_height - reference_height) > height_threshold:
            print("CORNER Difference: " + str(abs(self.avg_height - reference_height)))
            print("Height threshold: " + str(height_threshold))
            self.set_incorrect()
        else:
            print("CORNER Difference: " + str(abs(self.avg_height - reference_height)))
            print("Height threshold: " + str(height_threshold))
            # print("Difference: " + str(abs(self.avg_height - reference_height)))
            # print("Height threshold: " + str(height_threshold))
            self.set_correct()

        return abs(self.avg_height - reference_height)

    def equal(self, position):
        return self.position == position

    def set_correct(self):
        self.colors[:, 0] = 0
        self.correct = True

    def set_incorrect(self):
        self.colors[:, 0] = 1
        self.correct = False

    def log(self):
        logger.info(
            "Corner: "
            + str(self.position)
            + ", average height: "
            + str(self.avg_height)
        )

    def set_color(self):
        self.colors[:, 0] = 0
