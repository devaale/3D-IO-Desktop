from ..app.database import db_session
from ..models.corner import *
from threading import Lock

lock = Lock()


def add_corner(position, average_height, reference_id):
    # with lock:
    corner = Corner(position, average_height, reference_id)

    db_session.add(corner)

    db_session.commit()


def update_corner(position, average_height, reference_id):
    corners = list(
        Corner.query.filter(
            (Corner.reference_id == reference_id) & (Corner.position == position)
        )
    )

    corner = list(
        filter(
            lambda x: x.position == position and x.reference_id == reference_id, corners
        )
    )[0]

    corner.average_height = average_height

    db_session.commit()


def get_corners(reference_id):
    # with lock:
    corners = Corner.query.filter(Corner.reference_id == reference_id).all()
    filtered_corners = list(
        filter(
            lambda x: x.reference_id == reference_id,
            corners,
        )
    )
    return filtered_corners
