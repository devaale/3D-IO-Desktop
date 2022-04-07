from typing import List
import pathlib

# import keyboard
import os
import time
from enum import Enum, auto
import open3d as o3d
from viewer_app.visualization import Visualization
from pathlib import Path

COUNT = 0
ROOT_DIR = Path(__file__).parent.parent
EXCLUDE_FILE = "__init__.py"
DETECTION_RESULT_FOLDER = os.path.join(ROOT_DIR, "saved_data/detection/")
DETECTION_FOLDERS = [
    "original",
    "processed",
    "clustered",
    "clustered_modified",
    "result",
]
REFERENCE_RESULT_FOLDER = os.path.join(ROOT_DIR, "saved_data/reference/")

visualizer = Visualization()


class CloudType(Enum):
    RESULT = auto()
    REFERENCE = auto()


def get_clouds_directory(type: CloudType) -> List[str]:
    if type is CloudType.RESULT:
        return DETECTION_RESULT_FOLDER
    elif type is CloudType.REFERENCE:
        return REFERENCE_RESULT_FOLDER
    else:
        return DETECTION_RESULT_FOLDER


def get_files_by_date(
    directory: str, count: int = -1, reverse: bool = False
) -> List[str]:
    reference_files = []

    list_of_files = filter(
        lambda x: os.path.isfile(os.path.join(directory, x)), os.listdir(directory)
    )

    list_of_files = sorted(
        list_of_files,
        key=lambda x: os.path.getmtime(os.path.join(directory, x)),
        reverse=reverse,
    )

    for file_name in list_of_files:
        file_path = os.path.join(directory, file_name)
        if EXCLUDE_FILE in file_path:
            continue
        reference_files.append(file_path)

    return reference_files[:count] if count > 0 else reference_files


def get_detection_files(directory: str) -> List[str]:
    all_files = []

    for folder in DETECTION_FOLDERS:
        full_path = os.path.join(directory, folder)
        camera_files = get_files_by_date(full_path, count=2, reverse=True)
        all_files += camera_files

    camera_one_files = all_files[::2]
    camera_two_files = all_files[1::2]

    return camera_two_files + camera_one_files


def get_file_to_read(files: List[str], index: int):
    try:
        return files[index]
    except Exception as e:
        print("No such file, index: ", index)
        return None


def visualize_cloud(type: CloudType, count: int):
    # directory = get_clouds_directory(type)
    # files = (
    #     get_files_by_date(directory)
    #     if type is CloudType.REFERENCE
    #     else get_detection_files(directory)
    # )
    # file_to_read = get_file_to_read(files, count)
    # if file_to_read is None:
    #     return

    path = "C:/Users/evald/Documents/Coding/Projects/University/3D-IO-Desktop/viewer_app/original_cloud_2_0_2022-04-05__7_23_2_828709.pcd"

    cloud = o3d.io.read_point_cloud(path)
    print(cloud.get_max_bound())
    print(cloud.get_min_bound())
    o3d.visualization.draw_geometries([cloud])


def visualize_single_cloud(path):
    cloud = o3d.io.read_point_cloud(path)
    print("[READ FILE]: ", os.path.basename(path))

    o3d.visualization.draw_geometries([cloud])


def get_item_count_dir() -> int:
    initial_count = 0
    for path in pathlib.Path(REFERENCE_RESULT_FOLDER).iterdir():
        if path.is_file():
            initial_count += 1

    return initial_count


def start():
    type = CloudType.RESULT
    count = 0
    read = True
    print(ROOT_DIR)

    for i in range(get_item_count_dir()):
        visualize_cloud(CloudType.REFERENCE, i)

        # visualize_single_cloud(
        #     "/home/adminas/Documents/teltonika_gsm_surinkimas/saved_data/detection/result/result_cloud_2_0_2021-12-09__17_23_38_823217.pcd"
        # )


if __name__ == "__main__":
    start()
