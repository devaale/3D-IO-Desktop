from datetime import date, datetime
from os import X_OK, stat
from typing import List

import numpy as np
import open3d
from sqlalchemy import util
from desktop_app.models.product import Product

from desktop_app.services.camera import visualization
from desktop_app.services.camera.processing import product_processing
from desktop_app.gui import data_reader

from desktop_app.common import utils
from .models.result import Result
from .data_saver import DataSaver
from .processing import cloud_processing

from ...helpers import result_helper
from ...common.decorators import timing
from ...common.logger import logger
import open3d as o3d

SCAN_REGION_COUNT = 3


def get_axis_aligned_bounding_box(
    box_points: [],
) -> open3d.geometry.AxisAlignedBoundingBox:
    points_v3v = open3d.utility.Vector3dVector(box_points)
    return open3d.geometry.AxisAlignedBoundingBox.create_from_points(points_v3v)


@timing
def average_product_depth(products):
    summed_products = products[0]
    other_products = products[1:]
    for summed_product in summed_products:
        for other_product_group in other_products:
            for other_product in other_product_group:
                if (
                    summed_product.position == other_product.position
                    and summed_product.row_position == other_product.row_position
                ):
                    summed_product.sum_corners_average_heights(other_product.corners)

    return summed_products


@timing
def extract_products_from_frame(
    depth_frames, zone, camera_intrinsics, settings, selected_product
):
    reference_file = open(
        "reference_" + str(selected_product.product_type) + "_" + str(1) + ".txt", "r"
    )
    lines = reference_file.readlines()
    stripped_lines = [line.strip() for line in lines]

    all_points = []
    for x in range(len(stripped_lines)):
        if x % 9 == 0:
            index = x
        else:
            point = stripped_lines[x].split()
            all_points.append(point)

    bounding_boxes_points = np.array_split(
        all_points, int(selected_product.row_count) * selected_product.col_count
    )
    bounding_boxes = []
    all_geometries = []

    for box_points in bounding_boxes_points:
        bounding_box = get_axis_aligned_bounding_box(box_points)
        all_geometries.append(bounding_box)
        bounding_boxes.append(bounding_box)

    print("Amount of bounding boxes: ", len(bounding_boxes))
    # CROP BOUDNDING BOXES FROM THE CLOUD
    cloud = o3d.geometry.PointCloud()
    for depth_frame in depth_frames:
        cloud += cloud_processing.process_cloud(
            camera_intrinsics, depth_frame, settings
        )
    cloud_processing.rotate_cloud_correct_position(cloud)

    all_geometries.append(cloud)
    o3d.visualization.draw_geometries(all_geometries)
    clusters = []

    for box in bounding_boxes:
        cluster = cloud.crop(box)
        clusters.append(cluster)

    products = product_processing.create_products(
        clusters,
        selected_product.row_count,
        selected_product.col_count,
        settings["distance_ground"],
        settings["corner_size"],
    )
    # cloud = utils.sum_clouds(clusters)
    # o3d.visualization.draw_geometries([cloud])
    return products, clusters


@timing
def extract_products_for_detection(
    depth_frame,
    camera_intrinsics,
    settings,
    selected_product,
):
    reference_file = open("reference.txt", "r")
    lines = reference_file.readlines()
    stripped_lines = [line.strip() for line in lines]

    all_points = []
    for x in range(len(stripped_lines)):
        if x % 9 == 0:
            index = x
        else:
            point = stripped_lines[x].split()
            all_points.append(point)

    bounding_boxes_points = np.array_split(
        all_points, int(selected_product.row_count // 3) * selected_product.col_count
    )
    bounding_boxes = []

    for box_points in bounding_boxes_points:
        bounding_box = get_axis_aligned_bounding_box(box_points)
        bounding_boxes.append(bounding_box)

    # CROP BOUDNDING BOXES FROM THE CLOUD
    cloud = cloud_processing.process_cloud(camera_intrinsics, depth_frame, settings)
    cloud_processing.rotate_cloud_correct_position(cloud)
    clusters = []

    for box in bounding_boxes:
        cluster = cloud.crop(box)
        clusters.append(cluster)

    products = product_processing.create_products(
        clusters,
        selected_product.row_count,
        selected_product.col_count,
        settings["distance_ground"],
        settings["corner_size"],
    )

    print("Extracted product count: ", len(products))

    return products, clusters


@timing
def compare_to_refs(
    depth_frame,
    camera_intrinsics,
    settings,
    products,
    clusters,
    references,
    selected_product,
    scan_number,
    detection_results,
    detection_results_db,
    detection_results_folder,
):
    avg_height_differences = []
    max_height_differences = []

    print("Products: ", len(products))
    print("References: ", len(references))

    product_index = 0
    for product in products:
        for reference in references:
            if (
                product.position == reference.position
                and product.row_position == reference.row_position
            ):
                avg_diff = product.compare(reference, settings["accuracy"])
                avg_height_differences.append(avg_diff)

                print(
                    "Product: ",
                    product.position,
                    ", row: ",
                    product.row_position,
                    ", is correct: ",
                    product.correct,
                )
                max_height_difference = product.compare_max_height(
                    reference.max_height, settings["accuracy"]
                )

                max_height_differences.append(max_height_difference)

                add_result(
                    detection_results,
                    product.correct,
                    product.position,
                    product.row_position,
                    selected_product.row_count * selected_product.col_count,
                    scan_number,
                    product_index,
                )
        product_index += 1

    print("Max deviation from reference: ", np.max(avg_height_differences))
    print("Avg. deviation from references: ", np.average(avg_height_differences))

    print("Max height difference: ", np.max(max_height_differences))
    print("Max height difference: ", np.average(max_height_differences))
    # print("Min deviaton from references: ", np.min(avg_height_differences))

    shared_cloud = utils.sum_clouds(clusters)

    save_result_bounding_box(
        depth_frame,
        camera_intrinsics,
        settings,
        products,
        selected_product,
        scan_number,
        datetime.now(),
        detection_results_db,
        detection_results_folder,
        shared_cloud,
    )

    return products


@timing
def detect(
    depth_frame,
    camera_intrinsics,
    settings,
    references,
    selected_product,
    scan_number,
    detection_results,
    detection_results_db,
    detection_results_folder,
    detect_from_boxes: bool = False,
):
    if detect_from_boxes:
        # cloud = data_reader.read_reference_cloud_detection(1, 1)
        print("Reference count: ", len(references))
        reference_file = open("reference.txt", "r")
        lines = reference_file.readlines()
        stripped_lines = [line.strip() for line in lines]
        print("Stripped lines count: ", len(stripped_lines))

        all_points = []
        for x in range(len(stripped_lines)):
            if x % 9 == 0:
                index = x
            else:
                point = stripped_lines[x].split()
                all_points.append(point)

        bounding_boxes_points = np.array_split(all_points, 18)
        bounding_boxes = []

        for box_points in bounding_boxes_points:
            print("Points inside the box: ", len(box_points))
            print("Box points: ", box_points)
            print("===========================================")

            bounding_box = get_axis_aligned_bounding_box(box_points)
            bounding_boxes.append(bounding_box)

        # CROP BOUDNDING BOXES FROM THE CLOUD
        cloud = cloud_processing.process_cloud(camera_intrinsics, depth_frame, settings)
        cloud_processing.rotate_cloud_correct_position(cloud)
        clusters = []

        for box in bounding_boxes:
            cluster = cloud.crop(box)
            clusters.append(cluster)
        print("Clusters extracted: ", len(clusters))

        products = product_processing.create_products(
            clusters,
            selected_product.row_count * 3,
            selected_product.col_count,
            settings["distance_ground"],
            settings["corner_size"],
        )

        for product in products:
            for reference in references:
                if (
                    product.position == reference.position
                    and product.row_position == reference.row_position
                ):
                    product.compare(reference, settings["accuracy"])
                    print(
                        "Product: ",
                        product.position,
                        ", row: ",
                        product.row_position,
                        ", is correct: ",
                        product.correct,
                    )
                    # product.compare_max_height(
                    #     reference.max_height, settings["accuracy"]
                    # )

                    add_result(
                        detection_results,
                        product.correct,
                        product.position,
                        product.row_position,
                        selected_product.row_count * selected_product.col_count,
                        scan_number,
                    )

        print("Created products: ", len(products))

        shared_cloud = utils.sum_clouds(clusters)

        save_result_bounding_box(
            depth_frame,
            camera_intrinsics,
            settings,
            products,
            selected_product,
            scan_number,
            datetime.now(),
            detection_results_db,
            detection_results_folder,
            shared_cloud,
        )

        # all_geometries = []
        # all_geometries.append(cloud)
        # all_geometries += bounding_boxes
        # open3d.visualization.draw_geometries(all_geometries)

        return

    references_copy = references.copy()

    products = cloud_processing.extract_products_from_frame(
        depth_frame, camera_intrinsics, settings, selected_product
    )
    for product in products:
        for reference in references_copy:
            if (
                product.position == reference.position
                and product.row_position == reference.row_position
            ):
                product.compare(reference, settings["accuracy"])
                add_result(
                    detection_results,
                    product.correct,
                    product.position,
                    product.row_position,
                    selected_product.row_count * selected_product.col_count,
                    scan_number,
                )
    if scan_number == SCAN_REGION_COUNT:
        if selected_product.row_count * selected_product.col_count == 9:
            fill_results(detection_results)

    save_result(
        depth_frame,
        camera_intrinsics,
        settings,
        products,
        selected_product,
        scan_number,
        datetime.now(),
        detection_results_db,
        detection_results_folder,
    )

    return products


def save_result_bounding_box(
    depth_frame,
    camera_intrinsics,
    settings,
    products,
    selected_product,
    scan_number,
    datetime,
    detection_results_db: list,
    detections_results_folder,
    cloud,
):
    result_saver = DataSaver(detections_results_folder)
    result = Result(scan_number, datetime, selected_product.id)
    detection_results_db.append(result)
    result_saver.save_detection_bounding_boxes(
        depth_frame,
        camera_intrinsics,
        selected_product.product_type,
        scan_number,
        datetime,
        cloud,
    )

    result_saver.save_product_cloud(
        products, selected_product.product_type, scan_number, datetime
    )


def fill_results(detection_results: dict):
    for i in range(9, 18):
        detection_results[i] = False


def add_result(
    detection_results: dict,
    value: bool,
    col_position: int,
    row_position: int,
    total_products: int,
    scan_number: int,
    index=0,
):
    offset_bit = utils.get_offset_bit_reversed(
        col_position, row_position, total_products, scan_number
    )
    detection_results[index] = value


def save_result(
    depth_frame,
    camera_intrinsics,
    settings,
    products,
    selected_product,
    scan_number,
    datetime,
    detection_results_db: list,
    detections_results_folder,
):
    result = Result(scan_number, datetime, selected_product.id)
    detection_results_db.append(result)
    result_saver = DataSaver(detections_results_folder)
    # result_helper.add(scan_number, datetime, selected_product.id)
    result_saver.save_raw_frame(
        depth_frame, selected_product.product_type, scan_number, datetime
    )
    result_saver.save_original_cloud(
        depth_frame,
        camera_intrinsics,
        selected_product.product_type,
        scan_number,
        datetime,
    )
    result_saver.save_processed_cloud(
        depth_frame,
        camera_intrinsics,
        settings,
        selected_product.product_type,
        scan_number,
        datetime,
    )
    result_saver.save_product_cloud(
        products, selected_product.product_type, scan_number, datetime
    )
