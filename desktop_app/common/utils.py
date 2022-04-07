from typing import List
import itertools
import pyrealsense2 as rs
import open3d as o3d
import numpy as np
import math
from pathlib import Path
from desktop_app.services.camera.models.zone import Zone
from desktop_app.services.camera.models.zone_block import ZoneBlock

from desktop_app.services.camera.models.reference import Reference
from desktop_app.services.camera.models.bounding_box import BoundingBox


def normals_vectors_angle(first: [4], second: [4]) -> float:
    return math.fabs(sum(first[0:3] * second[0:3])) / (
        math.sqrt(sum(np.square(first[0:3]))) * math.sqrt(sum(np.square(second[0:3])))
    )


def angle_to_degrees(angle: float) -> float:
    return round(np.degrees(angle * np.pi / 2), 4)


def centroid(points: []) -> [3]:
    return np.mean(np.array(points), axis=0)


def get_root_directory() -> Path:
    return Path(__file__).parent.parent


def datetime_string(datetime):
    date = str(datetime.date())
    time = datetime.time()
    hours = str(time.hour)
    minutes = str(time.minute)
    seconds = str(time.second)
    microseconds = str(time.microsecond)

    return date + "__" + hours + "_" + minutes + "_" + seconds + "_" + microseconds


def format_file_name(
    directory,
    folder,
    file_name,
    product_type: int,
    camera_pos: int,
    datetime,
    extension,
) -> str:
    full_path = (
        directory
        + folder
        + file_name
        + str(product_type)
        + "_"
        + str(camera_pos)
        + "_"
        + datetime_string(datetime)
        + extension
    )
    return full_path


def format_reference_file_name(
    directory, file_name, product_type: int, camera_pos: int, cloud_type: str, extension
) -> str:
    product_type = int(product_type)

    full_path = (
        directory
        + file_name
        + "_"
        + str(int(product_type))
        + "_"
        + str(camera_pos)
        + "_"
        + str(cloud_type)
        + extension
    )

    return full_path


def format_file_name_no_ext(
    directory, folder, file_name, product_type, scan_number, datetime
) -> str:
    full_path = (
        directory
        + folder
        + file_name
        + str(product_type)
        + "_"
        + str(scan_number)
        + "_"
        + datetime_string(datetime)
    )
    return full_path


def closest_point_index(point: [3], points: []) -> int:
    points = np.aspoints
    distances = np.sum((points - point) ** 2, axis=1)
    return np.argmin(distances)


def get_offset_bit(
    col_position: int, row_position: int, total_products: int, scan_number: int
) -> int:
    if total_products == 18:
        return scan_number * ((scan_number - 1) * 3) + col_position + (row_position * 3)
    if total_products == 9:
        return ((scan_number - 1) * 3) + col_position + (row_position * 3)


def get_row_col_pos_by_index(index: int, col_count: int):
    row_pos = index // col_count
    col_pos = index % col_count

    return row_pos, col_pos


def get_reverse_mapped_position(
    col_position: int, row_position: int, total_products: int, scan_number: int
) -> int:
    if total_products == 9:
        return total_products - (scan_number * 3) - (row_position * 3) + col_position
    if total_products == 18:
        return (
            total_products
            - (scan_number * 3)
            - ((scan_number - 1) * 3)
            - (row_position * 3)
            + col_position
        )


def bounded_points(points: [], min_x: float, max_x: float, min_y: float, max_y: float):
    points_bounded = points[
        (points[:, 0] >= min_x)
        & (points[:, 0] <= max_x)
        & (points[:, 1] >= min_y)
        & (points[:, 1] <= max_y)
    ]
    return points_bounded


def box_within_y_bounds(
    bounding_box: BoundingBox,
    position: int,
    fraction_size: float,
    min_y: float,
    max_y: float,
) -> BoundingBox:
    min_x = fraction(bounding_box.min_x, bounding_box.max_x, position * fraction_size)
    max_x = fraction(
        bounding_box.min_x, bounding_box.max_x, (position + 1) * fraction_size
    )

    min_z, max_z = bounding_box.min_z, bounding_box.max_z

    corner_points = bounds_to_corner_points(min_x, max_x, min_y, max_y, min_z, max_z)

    box = BoundingBox([min_x, min_y, min_z], [max_x, max_y, max_z], corner_points)

    return box


def corner_min_max_x(bounding_box: BoundingBox, position: int, size: float):
    if position == 0 or position == 1:
        min_x = bounding_box.min_x
        max_x = fraction(bounding_box.min_x, bounding_box.max_x, size)
    elif position == 2 or position == 3:
        min_x = fraction(bounding_box.max_x, bounding_box.min_x, size)
        max_x = bounding_box.max_x
    else:
        min_x = bounding_box.min_x
        max_x = bounding_box.max_x

    return min_x, max_x


def corner_min_max_y(bounding_box: BoundingBox, position: int, size: float):
    if position == 0 or position == 2:
        min_y = bounding_box.min_y
        max_y = fraction(bounding_box.min_y, bounding_box.max_y, size)
    elif position == 1 or position == 3:
        min_y = fraction(bounding_box.max_y, bounding_box.min_y, size)
        max_y = bounding_box.max_y
    else:
        min_y = bounding_box.min_x
        max_y = bounding_box.max_x

    return min_y, max_y


def fraction(from_point, to_point, fraction_size) -> float:
    return from_point * (1 - fraction_size) + to_point * fraction_size


def sum_clouds(clouds: [o3d.geometry.PointCloud]) -> o3d.geometry.PointCloud:
    shared_cloud = o3d.geometry.PointCloud()

    for cloud in clouds:
        shared_cloud += cloud

    return shared_cloud


# Can use for each zone, try 5x5 sample concat and test results.
def calculate_mse(samples, predictions, axis: int = 0):
    samples = np.array(samples)
    predictions = np.array(predictions)

    return (np.square(samples - predictions)).mean(axis=axis)


def calculate_rmse(samples, predictions, axis: int = 0):
    samples = np.array(samples)
    predictions = np.array(predictions)

    return np.sqrt((samples - predictions).mean(axis=axis))


def cloud_from_points_colors(points, colors):
    cloud = o3d.geometry.PointCloud()

    cloud.points = o3d.utility.Vector3dVector(np.asarray(points))
    cloud.colors = o3d.utility.Vector3dVector(np.asarray(colors))

    return cloud


def sum_zones_blocks_points_colors_to_cloud(zones: List[ZoneBlock]):
    shared_cloud = o3d.geometry.PointCloud()

    for zone in zones:
        zone_cloud = o3d.geometry.PointCloud()

        zone_cloud.points = o3d.utility.Vector3dVector(np.asarray(zone.points))

        zone_cloud.colors = o3d.utility.Vector3dVector(np.asarray(zone.colors))

        shared_cloud += zone_cloud

    return shared_cloud


def sum_zones_points_colors_to_cloud(zones: List[Zone]):
    shared_cloud = o3d.geometry.PointCloud()

    for zone in zones:
        zone_cloud = o3d.geometry.PointCloud()

        zone_cloud.points = o3d.utility.Vector3dVector(np.asarray(zone.points))

        zone_cloud.colors = o3d.utility.Vector3dVector(np.asarray(zone.colors))

        shared_cloud += zone_cloud

    return shared_cloud


def sum_points_colors_to_cloud(items):
    if items is None:
        return

    shared_cloud = o3d.geometry.PointCloud()

    for item in items:
        for corner in item.corners:
            points = np.asarray(shared_cloud.points)

            colors = np.asarray(shared_cloud.colors)

            corner_points = np.asarray(corner.points)

            corner_colors = np.asarray(corner.colors)

            shared_cloud.points = o3d.utility.Vector3dVector(
                np.vstack((points, corner_points))
            )

            shared_cloud.colors = o3d.utility.Vector3dVector(
                np.vstack((colors, corner_colors))
            )

    return shared_cloud


def group_references(
    references: List[Reference], row_count: int, col_count: int, zone_count: int
) -> List[List[Reference]]:
    row_count = int(row_count / zone_count)
    row_indexes = np.arange(0, row_count)
    col_indexes = np.arange(0, col_count)

    grouped_references = []

    for pos_tuple in itertools.product(col_indexes, row_indexes):
        reference_group = list(
            filter(lambda x: x.compare(pos_tuple[0], pos_tuple[1]), references)
        )
        grouped_references.append(reference_group)

    return grouped_references


def sum_references(reference_groups: List[List[Reference]]):
    summed_references = []
    for group in reference_groups:
        summed_reference = Reference(group[0].position, group[1].row_position)
        for reference in group:
            summed_reference.sum_corners_average_heights(reference.corners)
        summed_references.append(summed_reference)

    return summed_references


# def grid_row_col_boxes(grid: Grid):
#     boxes = []
#     rows_fraction_size = 1 / grid.row_count
#     cols_fraction_size = 1 / grid.col_count

#     for i in range(grid.row_count):
#         row_min_y = fraction(grid.bounding_box.min_y, grid.bounding_box.max_y, i * rows_fraction_size)
#         row_max_y = fraction(grid.bounding_box.min_y, grid.bounding_box.max_y, (i + 1) * rows_fraction_size)
#         for j in range(grid.col_count):
#             row_col_box = box_within_y_bounds(grid.bounding_box, j, cols_fraction_size, row_min_y, row_max_y)
#             boxes.append(row_col_box)

#     return boxes


def oriented_bounding_box(
    source: o3d.geometry.PointCloud,
    extent_mul_w: float = 1,
    extent_mul_h: float = 1,
    extent_mul_d: float = 1,
    center_add_w: float = 0,
    center_add_h: float = 0,
    center_add_d: float = 0,
) -> o3d.geometry.OrientedBoundingBox:

    axis_aligned_bounding_box = source.get_axis_aligned_bounding_box()

    base_extent = axis_aligned_bounding_box.get_extent()

    extent = np.array(
        [
            [base_extent[0] * extent_mul_w],
            [base_extent[1] * extent_mul_h],
            [base_extent[2] * extent_mul_d],
        ]
    )

    base_center = axis_aligned_bounding_box.get_center()

    center = np.array(
        [
            base_center[0] + center_add_w,
            base_center[1] + center_add_h,
            base_center[2] + center_add_d,
        ]
    )

    return o3d.geometry.OrientedBoundingBox(center, np.identity(3), extent)


def line_sets_from_bounding_boxes(boxes: [BoundingBox]) -> o3d.geometry.LineSet:
    index = 0
    points, lines, colors = [], [], []
    multiple_line_sets = o3d.geometry.LineSet()

    for box in boxes:
        points += box.corner_points
        lines += bounding_lines_starting_at(index * 8)
        colors += bounding_box_line_colors()
        index += 1

    multiple_line_sets.points = o3d.utility.Vector3dVector(points)
    multiple_line_sets.lines = o3d.utility.Vector2iVector(lines)
    multiple_line_sets.colors = o3d.utility.Vector3dVector(colors)

    return multiple_line_sets


def line_sets_from_items(items) -> o3d.geometry.LineSet:
    index = 0
    points, lines, colors = [], [], []
    multiple_line_sets = o3d.geometry.LineSet()

    for item in items:
        points += item.get_corner_points()
        lines += bounding_lines_starting_at(index * 8)
        colors += bounding_box_line_colors()
        index += 1

    multiple_line_sets.points = o3d.utility.Vector3dVector(points)
    multiple_line_sets.lines = o3d.utility.Vector2iVector(lines)
    multiple_line_sets.colors = o3d.utility.Vector3dVector(colors)

    return multiple_line_sets


def bounds_to_corner_points(
    min_x: float, max_x: float, min_y: float, max_y: float, min_z: float, max_z: float
):
    bot_lower_left = [min_x, min_y, min_z]
    bot_lower_right = [max_x, min_y, min_z]

    bot_upper_left = [min_x, max_y, min_z]
    top_lower_left = [min_x, min_y, max_z]

    top_upper_right = [max_x, max_y, max_z]
    top_upper_left = [min_x, max_y, max_z]

    top_lower_right = [max_x, min_y, max_z]
    bot_upper_right = [max_x, max_y, min_z]

    corner_points = [
        bot_lower_left,
        bot_lower_right,
        bot_upper_left,
        top_lower_left,
        top_upper_right,
        top_upper_left,
        top_lower_right,
        bot_upper_right,
    ]
    return corner_points


def bounding_lines_starting_at(last_index: int) -> [12]:
    local_start_index = last_index

    return [
        [local_start_index, local_start_index + 1],
        [local_start_index, local_start_index + 2],
        [local_start_index + 1, local_start_index + 7],
        [local_start_index + 2, local_start_index + 7],
        [local_start_index + 3, local_start_index + 5],
        [local_start_index + 3, local_start_index + 6],
        [local_start_index + 4, local_start_index + 5],
        [local_start_index + 4, local_start_index + 6],
        [local_start_index, local_start_index + 3],
        [local_start_index + 1, local_start_index + 6],
        [local_start_index + 2, local_start_index + 5],
        [local_start_index + 4, local_start_index + 7],
    ]


def bounding_box_lines() -> [12]:
    return [
        [0, 1],
        [0, 2],
        [2, 3],
        [1, 7],
        [4, 5],
        [5, 6],
        [6, 7],
        [4, 7],
        [0, 4],
        [1, 6],
        [2, 5],
        [3, 7],
    ]


def bounding_box_line_colors():
    return [[0, 0, 0] for _ in range(len(bounding_box_lines()))]


def points_to_vectors3d(points) -> o3d.utility.Vector3dVector:
    return o3d.utility.Vector3dVector(np.asarray(points))


def vectors3d_to_points(points) -> []:
    return np.asarray(points)


def days_to_seconds(days: int) -> int:
    return days * 86400
