from ctypes import util
from datetime import datetime
import logging
from os import stat
from typing import List, Union
from desktop_app.models.reference import Reference
from desktop_app.services.camera import row_helper
from desktop_app.services.camera.models.zone import Zone

from desktop_app.services.camera.processing import zone_processing
from desktop_app.services.camera.models.product import Product
from desktop_app.services.camera.settings_proxy import SettingsProxy

from desktop_app.common import utils
from .models.result import Result
from .data_saver import DataSaver
from .processing import cloud_processing

from ...common.decorators import timing
from ...common.logger import logger
import open3d as o3d


@timing
def detect(
    depth_frame,
    depth_frames,
    camera_position,
    camera_intrinsics,
    settings: SettingsProxy,
    references: Union[List[Reference], List[Zone]],
    selected_product,
    scan_number,
    detection_results,
    detection_results_db,
    detection_results_folder,
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

    for i in range(len(zones)):
        reference_blocks_depths = references[i].blocks_property_list("avg_depth")
        zone_blocks_depths = zones[i].blocks_property_list("avg_depth")
        
        references[i].mse = utils.calculate_mse(reference_blocks_depths, zone_blocks_depths, axis=0)
        references[i].rmse = utils.calculate_rmse(reference_blocks_depths, zone_blocks_depths, axis=0)

    for i in range(len(references)):
        print(references[i])
        
    products = []

    if len(products) == 0:
        logging.info("[Clustering Detection] Extracted 0 products.")
        fill_error_results(0, detection_results)
    else:
        fill_results(detection_results, selected_product)   
        save_result(
            depth_frame,
            camera_intrinsics,
            settings,
            products,
            selected_product,
            camera_position,
            datetime.now(),
            detection_results_db,
            detection_results_folder,
        )

    return products


def check_fill_results(selected_product: Product):
    return selected_product.col_count * selected_product.row_count

def fill_error_results(start: int, processing_results):
    for i in range(start, 18):

        processing_results[i] = False
def fill_results(processing_results, selected_product: Product):
    if not check_fill_results(selected_product):
        return
    
    start = selected_product.row_count * selected_product.col_count

    for i in range(start, 18):
        processing_results[i] = False


def add_result(
    detection_results: dict,
    value: bool,
    index: int,
    col_position: int,
    row_position: int,
    total_products: int,
    scan_number: int,
):
    offset_bit = utils.get_offset_bit_reversed(
        col_position, row_position, total_products, scan_number
    )
    print("Got offset_bit: ", index)
    detection_results[index] = value


def save_result(
    depth_frame,
    camera_intrinsics,
    settings: SettingsProxy,
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
