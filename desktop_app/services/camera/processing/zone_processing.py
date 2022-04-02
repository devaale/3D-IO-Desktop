from typing import List
import numpy as np
import open3d as o3d
from desktop_app.common import utils
from desktop_app.services.camera.settings_proxy import SettingsProxy
from desktop_app.services.camera.models.zone import Zone
from desktop_app.services.camera.models.zone_block import ZoneBlock
from desktop_app.services.camera.processing import cloud_processing

def extract_zones(cloud, settings: SettingsProxy):
    shared_product_cloud = cloud_processing.extract_max_cluster(cloud, 1, settings) #Could be used for getting max size prodduct cluster to later use max value as
            #bounding box to crop other products out of the cloud.
    zones = generate_zones(shared_product_cloud, zone_size=.1, distance_ground=settings.get("distance_ground"))

    return zones

def extract_zones_blocks(zones: List[Zone], settings: SettingsProxy):
    for zone in zones:
        # zone_cloud = utils.cloud_from_points_colors(zone.points, zone.colors)
        v3v_points = o3d.utility.Vector3dVector(np.asarray(zone.points))
        zone_cloud = o3d.geometry.PointCloud(v3v_points)
        zone.blocks = generate_zones(zone_cloud, zone_size=.5, distance_ground=settings.get("distance_ground"), create_zone_block=True)

    return zones

def generate_zones(cloud: o3d.geometry.PointCloud, zone_size: float, distance_ground: float, create_zone_block: bool = False) -> List[Zone]:
    box = cloud.get_axis_aligned_bounding_box()

    base_extent = box.get_extent()

    zone_extent = np.array(
        [
            [base_extent[0] * zone_size],
            [base_extent[1] * zone_size],
            [base_extent[2] * 1],
        ]
    )

    center = box.get_center()

    bounding_box = o3d.geometry.OrientedBoundingBox(center, np.identity(3), base_extent)

    zones = []

    zone_count = int(1 / zone_size)

    for i in range(zone_count):
        for j in range(zone_count):
            zone = generate_zone(i, j, box.get_min_bound(), box.get_max_bound(), zone_extent)
            zone_center = zone.get_center()
            zone_oriented = o3d.geometry.OrientedBoundingBox(zone_center, np.identity(3), zone_extent)
            zone_points = np.asarray(cloud.crop(zone_oriented).points)

            if len(zone_points) == 0:
                continue

            zone_average_depth = 0

            if len(zone_points) > 0:
                zone_average_depth = distance_ground - np.mean(zone_points, axis=0)[2]

            zone = ZoneBlock(i, j, zone_average_depth) if create_zone_block else Zone(i, j)
            zone.box = zone_oriented
            zone.points = zone_points
            zone.set_random_color()
            zones.append(zone)

    return zones

def generate_voxel_grid(cloud: o3d.geometry.PointCloud) -> o3d.geometry.VoxelGrid:
    scaled_cloud = cloud.scale(1 / np.max(cloud.get_max_bound() - cloud.get_min_bound()),
          center=cloud.get_center())

    grid = o3d.geometry.VoxelGrid.create_from_point_cloud(scaled_cloud, 0.005)

    return grid


def generate_zone(row: int, col: int, min_bound, max_bound, zone_extent): 
    min_x, max_x = get_zone_min_max_bound(min_bound[0], col, zone_extent[0])
    min_y, max_y = get_zone_min_max_bound(min_bound[1], row, zone_extent[1])

    # corners = utils.bounds_to_corner_points(min_x, max_x, min_y, max_y, min_bound[2], max_bound[2])
    
    min_bound = [min_x, min_y, min_bound[2]]
    max_bound = [max_x, max_y, max_bound[2]]
    # zone_box = BoundingBox([min_x, min_y, min_bound[2]], [max_x, max_y, max_bound[2]], corners)
    zone_aligned_box = o3d.geometry.AxisAlignedBoundingBox(np.asarray(min_bound, dtype=float), np.asarray(max_bound, dtype=float))

    return zone_aligned_box

def get_zone_min_max_bound(init_val: float, index: int, extent: float):
    min_value = init_val + (index * extent)
    max_value = min_value + extent

    return min_value, max_value
