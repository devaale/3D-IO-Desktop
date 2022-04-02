import open3d as o3d
import os
from typing import List
from desktop_app.common import utils

DIR_NAME = os.path.dirname(
    os.path.abspath(__file__ + "/../../services/camera/saved_data/detection/product")
)

REFERENCE_DIR_NAME = os.path.dirname(
    os.path.abspath(__file__ + "/../../services/camera/saved_data/reference/product")
)

RAW_FOLDER = "raw/"
RAW_FILE = "image_"

RESULT_FOLDER = "result/"
RESULT_FILE = "result_cloud_"

CLUSTERED_FOLDER = "clustered/"
CLUSTERED_FILE = "clustered_cloud_"

CLUSTERED_MODIFIED_FOLDER = "clustered_modified/"
CLUSTERED_MODIFIED_FILE = "clustered_modified_cloud_"

ORIGINAL_FOLDER = "original/"
ORIGINAL_FILE = "original_cloud_"

PROCESSED_FOLDER = "processed/"
PROCESSED_FILE = "processed_cloud_"

REFERENCE_FILE = "reference"


def read_reference_cloud(result_data) -> o3d.geometry.PointCloud:
    
    full_path = utils.format_reference_file_name(
        REFERENCE_DIR_NAME,
        REFERENCE_FILE,
        result_data.product_type,
        result_data.camera_pos,
        result_data.cloud_type,
        ".pcd",
    )

    print("Reading cloud: ", full_path)

    cloud = o3d.io.read_point_cloud(full_path)
    return cloud


def read_reference_cloud_detection(
    product_type, scan_number
) -> o3d.geometry.PointCloud:
    full_path = utils.format_reference_file_name(
        REFERENCE_DIR_NAME,
        REFERENCE_FILE,
        product_type,
        scan_number,
        ".pcd",
    )

    cloud = o3d.io.read_point_cloud(full_path)
    return cloud

def read_original_cloud(result_data):
    full_path = utils.format_file_name(
        DIR_NAME + "/",
        ORIGINAL_FOLDER,
        ORIGINAL_FILE,
        result_data.product_type,
        result_data.scan_number,
        result_data.datetime,
        ".pcd",
    )

    cloud = o3d.io.read_point_cloud(full_path)
    print(full_path)

    if len(cloud.points) == 0:
        return None

    return cloud


def read_processed_cloud(result_data):
    full_path = utils.format_file_name(
        DIR_NAME + "/",
        PROCESSED_FOLDER,
        PROCESSED_FILE,
        result_data.product_type,
        result_data.scan_number,
        result_data.datetime,
        ".pcd",
    )

    cloud = o3d.io.read_point_cloud(full_path)

    if len(cloud.points) == 0:
        return None

    return cloud

def read_clustered_cloud(result_data):
    full_path = utils.format_file_name(
        DIR_NAME + "/",
        CLUSTERED_FOLDER,
        CLUSTERED_FILE,
        result_data.product_type,
        result_data.scan_number,
        result_data.datetime,
        ".pcd",
    )

    cloud = o3d.io.read_point_cloud(full_path)

    if len(cloud.points) == 0:
        return None

    return cloud

def read_clustered_modified_cloud(result_data):
    full_path = utils.format_file_name(
        DIR_NAME + "/",
        CLUSTERED_MODIFIED_FOLDER,
        CLUSTERED_MODIFIED_FILE,
        result_data.product_type,
        result_data.scan_number,
        result_data.datetime,
        ".pcd",
    )

    cloud = o3d.io.read_point_cloud(full_path)

    if len(cloud.points) == 0:
        return None

    return cloud
def read_result_cloud(result_data):
    full_path = utils.format_file_name(
        DIR_NAME + "/",
        RESULT_FOLDER,
        RESULT_FILE,
        result_data.product_type,
        result_data.scan_number,
        result_data.datetime,
        ".pcd",
    )

    cloud = o3d.io.read_point_cloud(full_path)

    if len(cloud.points) == 0:
        return None

    return cloud
