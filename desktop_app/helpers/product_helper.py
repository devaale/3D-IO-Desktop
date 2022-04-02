from numpy import product
from ..app.database import db_session
from ..models.product import *


def add_product(data) -> bool:
    model = data["model"]
    row_count = data["row_count"]
    col_count = data["col_count"]

    exists = Product.query.filter(Product.model == model).first() is not None

    if exists:
        return False, 0

    product = Product(model, row_count, col_count)

    db_session.add(product)

    db_session.commit()

    return True, product.id


def add_product_from_thread(model, row_count, col_count):
    product = Product(model, row_count, col_count)

    db_session.add(product)

    db_session.commit()


def get_products_names():
    products = Product.query.all()
    names = []
    for product in products:
        names.append(product.model)

    return names


def get_product_by_model(model):
    product = Product.query.filter(Product.model == model).first()

    return product


def set_selected_product(id: int):
    selected_product = Product.query.get(id)

    selected_product.selected = True

    for product in Product.query.filter(Product.id != id):
        product.selected = False

    db_session.commit()


def get_product_by_type(type):
    product = Product.query.filter(Product.product_type == type).first()
    print("[DB] Got product: ", product.model)
    return product


def get_product_by_model(model):
    product = Product.query.filter(Product.model == model).first()
    return product


def get_product_has_reference(id: int) -> bool:
    return Product.query.get(id).has_reference


def update_has_reference(id: int):
    product = Product.query.get(id)
    
    product.has_reference = True

    db_session.commit()
