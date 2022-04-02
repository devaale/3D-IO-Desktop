from desktop_app.models.product import Product
from desktop_app.models.enums.product import ProductType


def get_camera_rows(camera_position: int, selected_product: Product):
    take_rows = (
        selected_product.camera_1_rows
        if camera_position == 0
        else selected_product.camera_2_rows
    )
    row_start = 0 if camera_position == 0 else selected_product.camera_1_rows

    return row_start, take_rows
