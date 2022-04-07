import cv2
import numpy as np


class VisualizerResult:
    WIDTH = 700
    HEIGHT = 340
    SPACING = 20
    GOOD_COLOR = (0, 255, 0)
    BAD_COLOR = (0, 0, 255)

    def __init__(self):
        self.background = np.zeros((self.HEIGHT, self.WIDTH, 3), np.uint8)
        self.result_view = np.zeros((self.HEIGHT, self.WIDTH, 3), np.uint8)

    def create(self):
        cv2.namedWindow("Rezultatai", cv2.WINDOW_NORMAL)
        cv2.imshow("Rezultatai", self.result_view)
        cv2.waitKey(1)

    def update(self, results: dict):
        for value in results.values():
            print("======================" + str(value))
        values = list(results.values())
        cols, rows = 3, len(results) // 3
        width, height = 100, 100
        self.result_view = self.background.copy()
        for i in range(cols):
            row_values = values[i::3]
            for j in range(rows):
                start = (i * width + i * self.SPACING, j * height + j * self.SPACING)
                end = (start[0] + width, start[1] + height)
                mid = (
                    ((end[0] - start[0]) / 2) + start[0] - self.SPACING,
                    ((end[1] - start[1]) / 2) + start[1],
                )
                color = self.GOOD_COLOR if row_values[j] is True else self.BAD_COLOR
                cv2.rectangle(self.result_view, start, end, color, -1)
                self.write_pos(self.result_view, i, j, cols, rows, mid)

        cv2.imshow("Rezultatai", self.result_view)
        cv2.waitKey(1)

    def write_pos(self, image, col, row, col_count, row_count, pos):
        index_list = list(range(col_count * row_count))
        index_list_reversed = index_list[::-1]
        starting_index = col_count - col - 1
        index = index_list_reversed[starting_index::col_count][row]

        cv2.putText(
            image,
            str(index),
            (int(pos[0]), int(pos[1])),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
            2,
        )

    def destroy(self):
        cv2.destroyAllWindows()
