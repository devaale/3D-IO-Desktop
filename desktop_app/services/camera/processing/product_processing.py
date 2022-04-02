from typing import List
import open3d as o3d
import numpy as np
from desktop_app.common import utils
from ..models.product import Product
from ..models.reference import Reference
from ..models.bounding_box import BoundingBox

from ....helpers import reference_helper, corner_helper, product_helper, plc_helper
from ....common.logger import logger


def create_products(
    clusters: List[o3d.geometry.PointCloud],
    row_start: int,
    col_count: int,
    distance_ground: float,
    corner_size: float,
):
    products = []
    row_index = -1

    geometries = []

    for i in range(len(clusters)):
        if i % col_count == 0:
            row_index += 1
        geometries = []
        oriented_bounding_box = utils.oriented_bounding_box(clusters[i])
        geometries.append(oriented_bounding_box)
        geometries.append(clusters[i])

        product_bounding_box = BoundingBox(
            oriented_bounding_box.get_min_bound(),
            oriented_bounding_box.get_max_bound(),
            oriented_bounding_box.get_box_points(),
        )

        product = Product(
            utils.vectors3d_to_points(clusters[i].points),
            product_bounding_box,
            i % col_count,
            row_start + row_index,
        )

        print(
            "CREATED PRODUCT, ROW ======== : ",
            (row_start + row_index),
            ", COL: ",
            (i % col_count),
            ", CENTER: ",
            clusters[i].get_center(),
        )

        product.set_corners(distance_ground, corner_size)

        products.append(product)

    return products


def create_product_references(
    samples: List[Product],
    row_start: int,
    take_rows: int,
    col_count: int,
    distance_to_ground: float,
) -> List[Reference]:
    references = []

    for row_pos in range(row_start, row_start + take_rows):
        for col_pos in range(col_count):
            product_reference = Reference(col_pos, row_pos)

            for sample in samples:
                if (
                    sample.position == product_reference.position
                    and sample.row_position == product_reference.row_position
                ):
                    product_reference.max_height = sample.max_height
                    for corner in sample.corners:
                        product_reference.accumulate_corner_average(
                            corner.points, distance_to_ground, corner.position
                        )

            product_reference.recalculate_corners_averages()
            references.append(product_reference)

    return references
