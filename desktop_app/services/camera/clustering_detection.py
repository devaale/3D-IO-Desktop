from datetime import datetime
from desktop_app.services.camera import row_helper

from desktop_app.models.product import Product as ProductDB
from desktop_app.services.camera.settings_proxy import SettingsProxy

from desktop_app.common import utils
from .models.result import Result
from .data_saver import DataSaver
from .processing import cloud_processing

from ...common.decorators import timing
from ...common.logger import logger
import open3d as o3d
import copy
from desktop_app.services.camera.models.enums.cloud_type import CloudType

MAX_PRODUCTS = 18
SCAN_REGION_COUNT = 3


@timing
def detect(
    depth_frame,
    depth_frames,
    camera_position,
    camera_intrinsics,
    settings: SettingsProxy,
    references,
    selected_product: ProductDB,
    detection_results,
    detection_results_db,
    detection_results_folder,
):
    clouds_to_save = []
    references_copy = references.copy()

    summed_cloud = o3d.geometry.PointCloud()

    for frame in depth_frames:
        summed_cloud += cloud_processing.process_cloud(
            camera_intrinsics, frame, settings
        )

    (
        cloud_to_process,
        original_cloud,
    ) = cloud_processing.check_special_case_pre_processing(
        summed_cloud, selected_product, settings, camera_position
    )

    # o3d.visualization.draw_geometries([summed_cloud])

    clouds_to_save.append((copy.deepcopy(original_cloud), CloudType.ORIGINAL))
    clouds_to_save.append((copy.deepcopy(cloud_to_process), CloudType.PROCESSED))

    row_start, take_rows = row_helper.get_camera_rows(camera_position, selected_product)

    products = cloud_processing.extract_products_from_cloud(
        cloud_to_process,
        settings,
        row_start,
        take_rows,
        selected_product,
        original_cloud=original_cloud,
        camera_pos=camera_position,
        clouds_to_save=clouds_to_save,
    )

    # cloud = utils.sum_points_colors_to_cloud(products)
    # o3d.visualization.draw_geometries([cloud])

    for index, product in enumerate(products):
        for reference in references_copy:
            if (
                product.position == reference.position
                and product.row_position == reference.row_position
            ):
                product.compare(reference, settings.get("accuracy"))
                product.say_hello()
                add_result(detection_results, product.correct, index)

    clouds_to_save.append(
        (utils.sum_points_colors_to_cloud(products), CloudType.RESULT)
    )

    total_products = selected_product.col_count * selected_product.row_count

    if len(products) == 0:
        fill_results(
            detection_results,
            row_start * selected_product.col_count,
            take_rows * selected_product.col_count,
            selected_product.col_count,
            total_products,
            value=False,
        )

    if check_fill_results(total_products, camera_position):
        fill_results(
            detection_results,
            total_products,
            MAX_PRODUCTS - total_products,
            selected_product.col_count,
            total_products,
            value=False,
        )

    datetime_now = datetime.now()

    data_saver = DataSaver(detection_results_folder)
    data_saver.save_clouds(
        clouds_to_save, selected_product.product_type, camera_position, datetime_now
    )

    result = Result(camera_position, datetime_now, selected_product.id)
    detection_results_db.append(result)

    return products


def check_fill_results(total_products: int, camera_pos: int):
    return total_products < 18 and camera_pos == 1


def fill_error_results(start: int, processing_results):
    for i in range(start, 18):
        processing_results[i] = False


def fill_results(
    processing_results,
    start: int,
    amount: int,
    col_count: int,
    total_products: int,
    value: bool,
):
    end = start + amount
    logger.info(
        "[Clustering Detection] Filling results, start: "
        + str(start)
        + ", end: "
        + str(end)
    )
    for i in range(start, end):
        row_pos, col_pos = utils.get_row_col_pos_by_index(i, col_count)
        print("Index: ", i, ", row:col = ", row_pos, ":", col_pos)
        add_result(processing_results, value, i, col_pos, row_pos, total_products, 1)


def add_result(detection_results: dict, value: bool, index: int):
    detection_results[index] = value


# def add_result(
#     detection_results: dict,
#     value: bool,
#     index: int,
#     col_position: int,
#     row_position: int,
#     total_products: int,
#     scan_number: int,
# ):
#     offset_bit = utils.get_reverse_mapped_position(
#         col_position, row_position, total_products, scan_number
#     )
#     detection_results[offset_bit] = value


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
    # REFACTOR THIS
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
