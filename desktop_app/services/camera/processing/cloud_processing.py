from logging import log
import logging
from multiprocessing import Value
import open3d as o3d
import numpy as np
import copy
import pyrealsense2 as rs
from typing import List, Dict, Set
from desktop_app.common.decorators import timing
from desktop_app.common.logger import logger
from desktop_app.helpers.settings_helper import Setting
from desktop_app.models.product import Product
from desktop_app.common import utils
from desktop_app.services.camera.models.enums.cloud_type import CloudType
from desktop_app.services.camera.models.product import Product as AppProduct

from desktop_app.services.camera.settings_proxy import SettingsProxy

from ....models.enums.product import ProductType
from . import product_processing


def extract_products_from_frame(
    depth_frame: rs.depth_frame,
    camera_intrinsics: rs.intrinsics,
    settings: SettingsProxy,
    selected_product,
):
    processed_cloud = process_cloud(camera_intrinsics, depth_frame, settings)

    clusters = divide_to_clusters(
        processed_cloud,
        selected_product.row_count,
        selected_product.col_count,
        settings,
    )

    products = product_processing.create_products(
        clusters,
        selected_product.row_count,
        selected_product.col_count,
        settings.get("distance_ground"),
        settings.get("corner_size"),
    )

    return products


def process_cloud(
    camera_intrinsics: rs.intrinsics,
    depth_frame: rs.depth_frame,
    settings: SettingsProxy,
) -> o3d.geometry.PointCloud:

    depth_cloud = create_cloud_from_frame(depth_frame, camera_intrinsics)

    processed_cloud = preprocess_cloud(depth_cloud, settings)

    # crop_precentage = [settings.get("crop_precentage_x"), settings.get("crop_precentage_y"), settings.get("crop_precentage_z")]
    # crop_push = [settings.get("crop_center_push_x"), settings.get("crop_center_push_y"), settings.get("crop_center_push_z")]
    # cropped_cloud = crop_ptc(processed_cloud, crop_precentage, crop_push)

    return processed_cloud


def create_cloud_from_frame(
    depth_frame: rs.depth_frame, camera_intrinsic: rs.intrinsics
) -> o3d.geometry.PointCloud:
    depth_array = np.asanyarray(depth_frame.get_data())

    open3d_depth_image = o3d.geometry.Image(depth_array)

    intrinsic = __pinhole_camera_intrinsic(camera_intrinsic)

    cloud = o3d.geometry.PointCloud.create_from_depth_image(
        open3d_depth_image, intrinsic
    )

    return cloud


def special_case_processing_FMB010(
    cloud: o3d.geometry.PointCloud, settings: SettingsProxy
):
    crop_precentile = [
        settings.get("crop_precentage_x"),
        settings.get("crop_precentage_y"),
        settings.get("crop_precentage_z"),
    ]

    center_push = [
        settings.get("crop_center_push_x"),
        settings.get("crop_center_push_y"),
        settings.get("crop_center_push_z"),
    ]

    cloud = crop_ptc(cloud, crop_precentile, center_push)
    return cloud


def special_case_processing_FMB920(
    cloud: o3d.geometry.PointCloud, settings: SettingsProxy
):
    crop_precentile = [
        settings.get("crop_precentage_x"),
        settings.get("crop_precentage_y"),
        settings.get("crop_precentage_z"),
    ]

    center_push = [
        settings.get("crop_center_push_x"),
        settings.get("crop_center_push_y"),
        settings.get("crop_center_push_z"),
    ]

    cloud = crop_ptc(cloud, crop_precentile, center_push)
    return cloud


def check_special_case_pre_processing(
    cloud: o3d.geometry.PointCloud,
    product: Product,
    settings: SettingsProxy,
    cam_pos: int,
):
    original_cloud = copy.deepcopy(cloud)

    if product.product_type == ProductType.FMB910.value:
        bound_value = (
            settings.get("depth_bound_1")
            if cam_pos == 0
            else settings.get("depth_bound_2")
        )
        original_bound = (
            settings.get("depth_to") if cam_pos == 0 else settings.get("depth_to_2")
        )
        bound = original_bound - bound_value
        cloud_to_process = remove_points(cloud, bound)
        return cloud_to_process, original_cloud

    return cloud, original_cloud


def check_special_cases(
    clusters,
    settings: SettingsProxy,
    selected_product,
    cloud: o3d.geometry.PointCloud = None,
    camera_pos: int = 0,
):
    final_clusters = []
    all_geometries = []

    if selected_product.product_type == ProductType.FMB010.value:
        for cluster in clusters:
            cropped = special_case_processing_FMB010(cluster, settings)
            final_clusters.append(cropped)
    elif selected_product.product_type == ProductType.FMB910.value:
        for cluster in clusters:
            depth_to_add = (
                settings.get("depth_bound_1")
                if camera_pos == 0
                else settings.get("depth_bound_2")
            )
            cropped, bounding_box = crop_ptc_add_depth(cloud, cluster, depth_to_add)
            final_clusters.append(cropped)
            all_geometries.append(bounding_box)

    all_geometries.append(cloud)
    # TODO: VIZ
    # o3d.visualization.draw_geometries(all_geometries)
    return final_clusters if len(final_clusters) > 0 else clusters


def crop_ptc_add_depth(
    source: o3d.geometry.PointCloud,
    cluster: o3d.geometry.PointCloud,
    depth_to_add: float,
) -> o3d.geometry.PointCloud:

    axis_aligned_bounding_box = cluster.get_axis_aligned_bounding_box()

    base_extent = axis_aligned_bounding_box.get_extent()

    extent = np.array(
        [
            [base_extent[0]],
            [base_extent[1]],
            [base_extent[2] + depth_to_add],
        ]
    )

    bounding_box = o3d.geometry.OrientedBoundingBox(
        axis_aligned_bounding_box.get_center(), np.identity(3), extent
    )

    return source.crop(bounding_box), bounding_box


def extract_products_from_cloud(
    cloud,
    settings: SettingsProxy,
    row_start: int,
    take_rows: int,
    selected_product,
    original_cloud: o3d.geometry.PointCloud = None,
    camera_pos: int = 0,
    clouds_to_save: list = [],
):

    clusters = divide_to_clusters(
        cloud, take_rows, settings, selected_product.product_type, camera_pos
    )

    if len(clusters) == 0:
        logging.error("[Cloud Processing] No clusters extracted.")
        return []
    else:
        logging.info(
            "[Cloud Processing] Amount of clusters extracted: " + str(len(clusters))
        )

    clouds_to_save.append((utils.sum_clouds(clusters), CloudType.CLUSTERED))

    final_clusters = []
    final_clusters += check_special_cases(
        clusters, settings, selected_product, original_cloud, camera_pos
    )

    clouds_to_save.append(
        (utils.sum_clouds(final_clusters), CloudType.CLUSTERED_MODIFIED)
    )

    # TODO: VIZ
    # o3d.visualization.draw_geometries([utils.sum_clouds(final_clusters)])

    products = product_processing.create_products(
        final_clusters,
        row_start,
        selected_product.col_count,
        settings.get("distance_ground"),
        settings.get("corner_size"),
    )

    return products


def rotate_cloud_correct_position(cloud: o3d.geometry.PointCloud):
    rotation_matrix = cloud.get_rotation_matrix_from_xyz((np.pi, 0, 0))

    center = cloud.get_center()

    cloud.rotate(rotation_matrix, center)


def create_image_from_frame(depth_frame: rs.depth_frame):
    depth_array = np.asanyarray(depth_frame.get_data())

    open3d_depth_image = o3d.geometry.Image(depth_array)

    return open3d_depth_image


def preprocess_cloud(
    cloud: o3d.geometry.PointCloud, settings: SettingsProxy
) -> o3d.geometry.PointCloud:
    voxel_down_value = settings.get("voxel_down")

    processed_cloud = cloud.voxel_down_sample(voxel_down_value)

    return processed_cloud


def __transform_clouds(clouds: List[o3d.geometry.PointCloud]):
    for cloud in clouds:
        cloud.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])


def remove_points(
    cloud: o3d.geometry.PointCloud, bound_bot: float
) -> o3d.geometry.PointCloud:
    cloud_points = np.asarray(cloud.points)

    print("Bound bot: ", bound_bot)

    bg_removed_points = cloud_points[(cloud_points[:, 2] < bound_bot - 0.0005)]

    cloud.points = o3d.utility.Vector3dVector(bg_removed_points)

    return cloud


def crop_ptc(
    source: o3d.geometry.PointCloud, crop_percentile, center_push
) -> o3d.geometry.PointCloud:

    axis_aligned_bounding_box = source.get_axis_aligned_bounding_box()

    base_extent = axis_aligned_bounding_box.get_extent()

    extent = np.array(
        [
            [base_extent[0] * crop_percentile[0]],
            [base_extent[1] * crop_percentile[1]],
            [base_extent[2] * crop_percentile[2]],
        ]
    )

    base_center = axis_aligned_bounding_box.get_center()

    center = np.array(
        [
            base_center[0] + center_push[0],
            base_center[1] + center_push[1],
            base_center[2] + center_push[2],
        ]
    )

    bounding_box = o3d.geometry.OrientedBoundingBox(center, np.identity(3), extent)

    return source.crop(bounding_box)


def extract_max_cluster(
    cloud: o3d.geometry.PointCloud, take_rows: int, settings: SettingsProxy
) -> List[o3d.geometry.PointCloud]:
    min_points_in_cluster = 10

    eps = settings.get("voxel_down") * 2

    points_clusters = __find_clusters(cloud, min_points_in_cluster, eps)

    max_cluster = __get_max_points_cluster(points_clusters)

    return max_cluster


def divide_to_clusters(
    cloud: o3d.geometry.PointCloud,
    take_rows: int,
    settings: SettingsProxy,
    product_type: int,
    camera_pos: int,
) -> List[o3d.geometry.PointCloud]:
    min_points_in_cluster = 10

    eps = settings.get("voxel_down") * 2

    # min_points_in_cloud = len(cloud.points) // int(params["min_points_cluster_divider"])

    points_clusters = __find_clusters(cloud, min_points_in_cluster, eps)

    max_cluster_points = __get_max_cluster_points(points_clusters)

    logger.info(
        "[Divide to Clusters]: Max. points in cluster: " + str(max_cluster_points)
    )

    if max_cluster_points == 0:
        logger.error("[Cloud Processing] No points in cloud")
        return []

    min_points_in_cloud = int(
        max_cluster_points * float(settings.get("precentage_of_average_points_cluster"))
    )

    print("[Divide to Clusters] Min points in clouds: ", min_points_in_cloud)

    clusters_clouds = __filter_clusters(points_clusters, min_points_in_cloud)

    print("[Divide to Clusters] Clusters filtered: ", len(clusters_clouds))

    sorted_height_clusters = __sort_clusters_by_single_axis(
        clusters_clouds, 1, reverse=True
    )

    if product_type == ProductType.FMB600.value and camera_pos == 1:
        sorted_height_clusters = sorted_height_clusters[-3:]

    if product_type == ProductType.FMB910.value and camera_pos == 1:
        items_to_take = 3 * take_rows
        sorted_height_clusters = sorted_height_clusters[-items_to_take:]

    clusters_for_detection = []

    for i in range(take_rows):
        cluster_for_detection = sorted_height_clusters[i * 3 : (i + 1) * 3]
        sorted_cluster_for_detection = __sort_clusters_by_single_axis(
            cluster_for_detection, 0, reverse=False
        )
        clusters_for_detection += sorted_cluster_for_detection

    return clusters_for_detection


@timing
def divide_to_planes(
    cloud: o3d.geometry.PointCloud,
    threshold_distance: float = 0.001,
    ransac_n: int = 3,
    iterations: int = 1000,
    planes_to_extract_count: int = 2,
):
    planes = []

    cloud_temp = cloud

    for _ in range(planes_to_extract_count):
        model, inliers = __export_plane_inliers(
            cloud_temp, threshold_distance, ransac_n, iterations
        )

        plane = cloud_temp.select_by_index(inliers)

        planes.append((plane, model))

        cloud_temp = cloud_temp.select_by_index(inliers, True)

        if len(cloud_temp.points) < 3:
            raise Exception("plane division error")

    if len(planes) < 2:
        raise Exception("only one plane extracted")

    return planes


def filter_planes(planes):
    planes.sort(key=__sort_planes_by_single_axis, reverse=True)

    return planes[0][0], planes[1][0], planes[1][1]


def __pinhole_camera_intrinsic(
    camera_intrinsic: rs.intrinsics,
) -> o3d.camera.PinholeCameraIntrinsic:
    return o3d.camera.PinholeCameraIntrinsic(
        camera_intrinsic.width,
        camera_intrinsic.height,
        camera_intrinsic.fx,
        camera_intrinsic.fy,
        camera_intrinsic.ppx,
        camera_intrinsic.ppy,
    )


def __find_clusters(
    cloud: o3d.geometry.PointCloud, min_points_in_cluster: int, eps: int
):
    labels = np.array(
        cloud.cluster_dbscan(
            min_points=min_points_in_cluster, eps=eps, print_progress=False
        )
    )
    points_clusters = {}

    for point, label in zip(cloud.points, labels):
        if label != -1:
            points_clusters[label] = points_clusters.get(label, [])
            points_clusters[label].append(point)

    print("[Cloud Processing] Clusters found: ", len(list(points_clusters.keys())))
    return points_clusters


def __filter_clusters(
    points_clusters, min_points_in_cloud: int
) -> List[o3d.geometry.PointCloud]:
    clusters_clouds = []

    for _, points_cluster in points_clusters.items():
        if len(points_cluster) > min_points_in_cloud:
            cluster_points = o3d.geometry.PointCloud(
                o3d.utility.Vector3dVector(points_cluster)
            )
            clusters_clouds.append(cluster_points)

    return clusters_clouds


def __get_max_points_cluster(points_clusters) -> o3d.geometry.PointCloud:
    try:
        points = max(points_clusters.values(), key=lambda x: len(x))
        return o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    except ValueError:
        return None


def __get_max_cluster_points(points_clusters) -> int:
    try:
        result = len(max(points_clusters.values(), key=lambda x: len(x)))
    except ValueError:
        return 0

    return result


def __sort_planes_by_single_axis(cloud_with_model, axis: int = 2):
    depth = cloud_with_model[0].get_center()[axis]
    return depth


def __sort_clusters_by_single_axis(
    clusters_clouds: List[o3d.geometry.PointCloud], axis: int = 0, reverse: bool = True
) -> List[o3d.geometry.PointCloud]:
    sorted_clusters = sorted(
        clusters_clouds, key=lambda x: x.get_center()[axis], reverse=reverse
    )

    return sorted_clusters


def __export_plane_inliers(
    cloud: o3d.geometry.PointCloud, threshold: float, ransac: int, iterations: int
):
    plane_model, inliers = cloud.segment_plane(threshold, ransac, iterations)
    return plane_model, inliers


def paint_clusters(sorted_clusters: [o3d.geometry.PointCloud]):
    index = -1
    colors = [
        [1, 0, 0],
        [0, 0, 0],
        [0, 1, 0],
        [0.4, 0.9, 0],
        [0.4, 0.3, 0],
        [0.7, 0.4, 0.2],
        [0.1, 0.7, 0.7],
        [0.1, 0.1, 0.6],
        [0.8, 0.4, 0.2],
        [0.5, 0.9, 0.4],
    ]

    colors_x = [[1, 0, 0], [1, 1, 0.2], [0.5, 0.9, 1]]

    temp_count = 0

    for cluster in sorted_clusters:
        if temp_count % 3 == 0:
            index += 1
        cluster.paint_uniform_color(colors[temp_count])
        temp_count += 1
