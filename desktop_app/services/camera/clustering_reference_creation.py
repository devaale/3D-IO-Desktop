from typing import List

from desktop_app.common.decorators import timing
import open3d as o3d
from desktop_app.models.product import Product
from desktop_app.common import utils
from desktop_app.services.camera.models.enums.cloud_type import CloudType
from desktop_app.services.camera.settings_proxy import SettingsProxy
from .models.corner import Corner
from .models.reference import Reference
from .data_saver import DataSaver
from .processing import cloud_processing, product_processing
from ...models.enums.product import ProductType
from ...helpers import corner_helper, reference_helper
from . import row_helper
from ...common.logger import logger
import copy

SCAN_REGION_COUNT = 3
MAX_PRODUCTS = 18


@timing
def create(
    depth_frame,
    depth_frames,
    camera_position,
    camera_intrinsics,
    settings: SettingsProxy,
    selected_product: Product,
    processing_results,
    processing_results_db,
    processing_results_folder,
):
    clouds_to_save = []
    summed_cloud = o3d.geometry.PointCloud()

    for frame in depth_frames:
        summed_cloud += cloud_processing.process_cloud(
            camera_intrinsics, frame, settings
        )

    # TODO: VIZ
    # o3d.visualization.draw_geometries([summed_cloud])

    (
        cloud_to_process,
        original_cloud,
    ) = cloud_processing.check_special_case_pre_processing(
        summed_cloud, selected_product, settings, camera_position
    )
    # TODO: VIZ
    # o3d.visualization.draw_geometries([cloud_to_process])

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

    # TODO: VIZ
    cloud = utils.sum_points_colors_to_cloud(products)
    # o3d.visualization.draw_geometries([cloud])

    clouds_to_save.append(
        (utils.sum_points_colors_to_cloud(products), CloudType.RESULT)
    )

    references = product_processing.create_product_references(
        products,
        row_start,
        take_rows,
        selected_product.col_count,
        settings.get("distance_ground"),
    )

    logger.info(
        "[Reference Creation Clustering] Extracted, references: " + str(len(references))
    )

    fill_results(processing_results)

    fill_results_db(references, processing_results_db)

    saver = DataSaver(processing_results_folder)
    saver.save_reference_clouds(
        clouds_to_save, selected_product.product_type, camera_position
    )

    return products


def fill_results_db(references: List[Reference], processing_results_db):
    for reference in references:
        processing_results_db.append(reference)


def fill_results(processing_results):
    for i in range(0, MAX_PRODUCTS):
        processing_results[i] = False


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
