from ctypes import util
from datetime import datetime
from logging import log
from typing import List

import numpy as np
import open3d as o3d
from desktop_app.common.decorators import timing
import open3d as o3d
from desktop_app.models.product import Product
from desktop_app.services.camera.models.zone import Zone
from desktop_app.services.camera.processing import zone_processing
from desktop_app.services.camera.settings_proxy import SettingsProxy
from .models.corner import Corner
from .models.reference import Reference
from .data_saver import DataSaver
from .processing import cloud_processing
from ...helpers import corner_helper, reference_helper
from desktop_app.common import utils
from ...common.logger import logger

SCAN_REGION_COUNT = 3

def get_train_predict_clouds(frames, intrinsics, settings, split_value: int = 2):
    train_cloud = o3d.geometry.PointCloud()
    predict_cloud = o3d.geometry.PointCloud()

    split_data = np.array_split(frames, split_value)
    
    
    for i in range(len(split_data[0])):
        train_cloud += cloud_processing.process_cloud(intrinsics, split_data[0][i], settings)
        predict_cloud += cloud_processing.process_cloud(intrinsics, split_data[1][i], settings)
    
    return train_cloud, predict_cloud


def calculate_statistics(train_zones: List[Zone], predict_zones: List[Zone]):

    for i in range(len(train_zones)):
        mse = utils.calculate_mse()



@timing
def create(
    depth_frame,
    depth_frames,
    camera_position,
    camera_intrinsics,
    settings: SettingsProxy,
    selected_product: Product,
    scan_number,
    processing_results,
    processing_results_db,
    processing_results_folder,
):
    summed_cloud = o3d.geometry.PointCloud()

    for frame in depth_frames:
        summed_cloud += cloud_processing.process_cloud(
            camera_intrinsics, frame, settings
        )

    row_start, take_rows = row_helper.get_camera_rows(camera_position, selected_product)

    zones = zone_processing.extract_zones(summed_cloud, settings)

    zones_with_blocks = zone_processing.extract_zones_blocks(zones, settings)
    
    zone_cloud = utils.sum_zones_points_colors_to_cloud(zones)

    zone_blocks_cloud = o3d.geometry.PointCloud()

    for zone in zones_with_blocks:
        zone_blocks_cloud += utils.sum_zones_blocks_points_colors_to_cloud(zone.blocks)

    o3d.visualization.draw_geometries([zone_cloud])
    # o3d.visualization.draw_geometries([zone_blocks_cloud])
    
    products = []

    add_result(
        False,
        row_start,
        take_rows,
        selected_product.col_count,
        processing_results,
    )

    fill_results(processing_results, selected_product)

    add_result_db([], processing_results_db)

    save_result(
        depth_frame,
        camera_intrinsics,
        settings,
        selected_product,
        scan_number,
        processing_results_folder,
    )

    return [], camera_position, zones_with_blocks


def add_result_db(references: List[Reference], processing_results_db):
    print("Reference count: ", len(references))
    for reference in references:
        processing_results_db.append(reference)


def add_result(
    value: bool,
    start: int,
    take_rows: int,
    col_count: int,
    processing_results,
):
    start_index = start * col_count
    end_index = start_index + (take_rows * col_count)
    for i in range(start_index, end_index):
        processing_results[i] = value

def check_fill_results(selected_product: Product):
    return selected_product.col_count * selected_product.row_count

def fill_results(processing_results, selected_product: Product):
    if not check_fill_results(selected_product):
        return
    
    start = selected_product.row_count * selected_product.col_count

    for i in range(start, 18):
        processing_results[i] = False

def save_result(
    depth_frame,
    camera_intrinsics,
    settings,
    selected_product,
    scan_number,
    processing_results_folder,
):
    result_saver = DataSaver(processing_results_folder)

    result_saver.save_reference_cloud(
        depth_frame,
        camera_intrinsics,
        settings,
        selected_product.product_type,
        scan_number,
    )


def get_references(product_id):
    references = reference_helper.get_references(product_id)
    references_result = []
    for reference in references:
        result_ref = Reference(reference.col_position, reference.row_position)
        corners = corner_helper.get_corners(reference.id)
        for corner in corners:
            result_corner = Corner(
                position=corner.position, avg_height=corner.average_height
            )
            result_ref.set_corner(result_corner, corner.position)
        references_result.append(result_ref)

    return references_result
