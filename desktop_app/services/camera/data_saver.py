from datetime import datetime
import open3d as o3d
from typing import List, Tuple
from pathlib import Path
from desktop_app.common.logger import logger
from desktop_app.services.camera.models.enums.cloud_type import CloudType
from desktop_app.services.camera.settings_proxy import SettingsProxy
from desktop_app.common import utils
from .processing import cloud_processing
import os


class DataSaver(object):

    ORIGINAL_FOLDER = "original/"
    ORIGINAL_FILE = "original_cloud_"

    PROCESSED_FOLDER = "processed/"
    PROCESSED_FILE = "processed_cloud_"

    CLUSTERED_FOLDER = "clustered/"
    CLUSTERED_FILE = "clustered_cloud_"

    CLUSTERED_MODIFIED_FOLDER = "clustered_modified/"
    CLUSTERED_MODIFIED_FILE = "clustered_modified_cloud_"

    RESULT_FOLDER = "result/"
    RESULT_FILE = "result_cloud_"

    REFERENCE_FILE = "reference"
    ROOT_DIR = Path(__file__).parent.parent.parent.parent

    def __init__(self, directory=None):
        self.__directory = (
            os.path.join(self.ROOT_DIR, directory)
            if not directory is None
            else directory
        )

    def save_clouds(
        self,
        clouds: List[Tuple[o3d.geometry.PointCloud, CloudType]],
        product_type: int,
        camera_pos: int,
        datetime: datetime,
    ):
        file = ""
        folder = ""

        for cloud, type in clouds:
            if type is CloudType.ORIGINAL:
                folder, file = self.ORIGINAL_FOLDER, self.ORIGINAL_FILE
            elif type is CloudType.PROCESSED:
                folder, file = self.PROCESSED_FOLDER, self.PROCESSED_FILE
            elif type is CloudType.CLUSTERED:
                folder, file = self.CLUSTERED_FOLDER, self.CLUSTERED_FILE
            elif type is CloudType.CLUSTERED_MODIFIED:
                folder, file = (
                    self.CLUSTERED_MODIFIED_FOLDER,
                    self.CLUSTERED_MODIFIED_FILE,
                )
            elif type is CloudType.RESULT:
                folder, file = self.RESULT_FOLDER, self.RESULT_FILE
            else:
                logger.warning("[Data Saver] No such type: " + str(type))

            path = utils.format_file_name(
                self.__directory,
                folder,
                file,
                product_type,
                camera_pos,
                datetime,
                ".pcd",
            )

            o3d.io.write_point_cloud(path, cloud)

    def save_detection_bounding_boxes(
        self,
        depth_frame,
        camera_instrinsics,
        product_type,
        scan_number,
        datetime,
        cloud,
    ):
        full_path = utils.format_file_name(
            self.__directory,
            self.PROCESSED_FOLDER,
            self.PROCESSED_FILE,
            product_type,
            scan_number,
            datetime,
            ".pcd",
        )

        o3d.io.write_point_cloud(full_path, cloud)

    def save_raw_frame(self, frame, product_type, scan_number, datetime):
        full_path = utils.format_file_name(
            self.__directory,
            self.RAW_FOLDER,
            self.RAW_FILE,
            product_type,
            scan_number,
            datetime,
            ".png",
        )

        image = cloud_processing.create_image_from_frame(frame)

        o3d.io.write_image(full_path, image)

    def save_original_cloud(
        self, depth_frame, camera_instrinsics, product_type, scan_number, datetime
    ):
        full_path = utils.format_file_name(
            self.__directory,
            self.ORIGINAL_FOLDER,
            self.ORIGINAL_FILE,
            product_type,
            scan_number,
            datetime,
            ".pcd",
        )

        pcd = cloud_processing.create_cloud_from_frame(depth_frame, camera_instrinsics)

        # cloud_processing.rotate_cloud_correct_position(pcd)

        o3d.io.write_point_cloud(full_path, pcd)

    def save_processed_cloud(
        self,
        depth_frame,
        camera_intrinsics,
        settings: SettingsProxy,
        product_type,
        scan_number,
        datetime,
    ):
        full_path = utils.format_file_name(
            self.__directory,
            self.PROCESSED_FOLDER,
            self.PROCESSED_FILE,
            product_type,
            scan_number,
            datetime,
            ".pcd",
        )

        pcd = cloud_processing.process_cloud(camera_intrinsics, depth_frame, settings)

        cloud_processing.rotate_cloud_correct_position(pcd)

        o3d.io.write_point_cloud(full_path, pcd)

    def save_reference_clouds(
        self,
        clouds: List[Tuple[o3d.geometry.PointCloud, CloudType]],
        product_type: int,
        camera_pos: int,
    ):
        for i, value in enumerate(clouds):
            path = utils.format_reference_file_name(
                self.__directory,
                self.REFERENCE_FILE,
                product_type,
                camera_pos,
                value[1].name,
                ".pcd",
            )
            print(path)
            o3d.io.write_point_cloud(path, value[0])

    def save_reference_cloud_only(self, cloud, product_type, scan_number):
        full_path = utils.format_reference_file_name(
            self.__directory,
            self.REFERENCE_FILE,
            product_type,
            scan_number,
            ".pcd",
        )

        # correct_cloud = cloud_processing.rotate_cloud_correct_position(cloud)

        o3d.io.write_point_cloud(full_path, cloud)

    def save_reference_cloud(
        self, depth_frame, camera_intrinsics, settings, product_type, scan_number
    ):
        print(self.REFERENCE_FILE, product_type, scan_number)
        full_path = utils.format_reference_file_name(
            self.__directory,
            self.REFERENCE_FILE,
            product_type,
            scan_number,
            ".pcd",
        )

        pcd = cloud_processing.process_cloud(camera_intrinsics, depth_frame, settings)

        cloud_processing.rotate_cloud_correct_position(pcd)

        o3d.io.write_point_cloud(full_path, pcd)

    def save_summed_reference_cloud(
        self, depth_frames, camera_intrinsics, settings, product_type, scan_number
    ):
        print(self.REFERENCE_FILE, product_type, scan_number)
        full_path = utils.format_reference_file_name(
            self.__directory,
            self.REFERENCE_FILE,
            product_type,
            scan_number,
            ".pcd",
        )

        full_pcd = o3d.geometry.PointCloud()

        for frame in depth_frames:
            full_pcd += cloud_processing.process_cloud(
                camera_intrinsics, frame, settings
            )

        cloud_processing.rotate_cloud_correct_position(full_pcd)

        o3d.io.write_point_cloud(full_path, full_pcd)

    def save_product_cloud(self, products, product_type, scan_number, datetime):
        full_path = utils.format_file_name(
            self.__directory,
            self.PRODUCT_FOLDER,
            self.PRODUCT_FILE,
            product_type,
            scan_number,
            datetime,
            ".pcd",
        )

        pcd = utils.sum_points_colors_to_cloud(products)

        # cloud_processing.rotate_cloud_correct_position(pcd)

        o3d.io.write_point_cloud(full_path, pcd)
