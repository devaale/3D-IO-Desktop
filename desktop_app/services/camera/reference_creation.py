from datetime import datetime
from typing import List

from numpy import result_type
from desktop_app.common.decorators import timing

from .models.corner import Corner
from .models.reference import Reference
from .data_saver import DataSaver
from .processing import cloud_processing, product_processing
from ...helpers import corner_helper, reference_helper
from ...common.logger import logger

SCAN_REGION_COUNT = 3


@timing
def create(
    depth_frame,
    depth_frames,
    camera_intrinsics,
    settings,
    selected_product,
    scan_number,
    processing_results,
    processing_results_db,
    processing_results_folder,
    save_only: bool = False,
) -> bool:
    if save_only:
        result_saver = DataSaver(processing_results_folder)

        # result_saver.save_reference_cloud(
        #     depth_frame,
        #     camera_intrinsics,
        #     settings,
        #     selected_product.product_type,
        #     scan_number,
        # )

        result_saver.save_summed_reference_cloud(
            depth_frames,
            camera_intrinsics,
            settings,
            selected_product.product_type,
            scan_number,
        )
        return

    # FOR clustering problem sum product data here
    products = cloud_processing.extract_products_from_frame(
        depth_frame, camera_intrinsics, settings, selected_product
    )

    references = product_processing.create_product_references(
        products,
        selected_product.row_count,
        selected_product.col_count,
        settings["distance_ground"],
    )

    add_result(
        True,
        selected_product.row_count * selected_product.col_count,
        scan_number,
        processing_results,
    )

    add_result_db(references, processing_results_db)

    save_result(
        depth_frame,
        camera_intrinsics,
        settings,
        products,
        selected_product,
        scan_number,
        datetime.now(),
        processing_results_folder,
    )

    return products


def add_result_db(references: List[Reference], processing_results_db):
    for reference in references:
        processing_results_db.append(reference)


def add_result(value: bool, total_products: int, scan_number: int, processing_results):
    start_index = int((total_products / SCAN_REGION_COUNT) * (scan_number - 1))
    end_index = int((total_products / SCAN_REGION_COUNT) * (scan_number))

    for i in range(start_index, end_index):
        processing_results[i] = value

    if scan_number == SCAN_REGION_COUNT:
        if total_products == 9:
            for i in range(9, 18):
                processing_results[i] = value


def save_processed_cloud_only(
    cloud, selected_product, scan_number, processing_results_folder
):
    result_saver = DataSaver(processing_results_folder)
    result_saver.save_reference_cloud_only(
        cloud, selected_product.product_type, scan_number
    )


def save_result(
    depth_frame,
    camera_intrinsics,
    settings,
    products,
    selected_product,
    scan_number,
    datetime,
    processing_results_folder,
):
    result_saver = DataSaver(processing_results_folder)

    print("Saving cloud, scan_number: ", scan_number)
    result_saver.save_reference_cloud(
        depth_frame,
        camera_intrinsics,
        settings,
        selected_product.product_type,
        scan_number,
    )


def get_references(product_id, partial: bool = False):
    references = reference_helper.get_references(product_id, partial)
    references_result = []
    for reference in references:
        result_ref = Reference(
            reference.col_position, reference.row_position, reference.max_height
        )
        corners = corner_helper.get_corners(reference.id)
        for corner in corners:
            result_corner = Corner(
                position=corner.position, avg_height=corner.average_height
            )
            result_ref.set_corner(result_corner, corner.position)
        references_result.append(result_ref)

    return references_result
