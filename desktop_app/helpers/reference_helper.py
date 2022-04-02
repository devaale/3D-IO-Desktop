from ..app.database import db_session
from ..models.reference import *
from . import corner_helper


def get_global_row_pos(local_row_pos, zone_number, rows_per_zone):
    if local_row_pos == 0:
        return rows_per_zone * (zone_number - 1)
    else:
        return local_row_pos + (rows_per_zone * (zone_number - 1))


def add_update_references_with_corners(
    references, product_id, zone_number, is_partial: bool = False
):
    for reference in references:
        reference_id = get_reference(
            reference.position,
            reference.row_position,
            product_id,
            zone_number,
            is_partial,
        )

        if reference_id is None:
            reference_id = add_reference(
                reference.position,
                reference.row_position,
                product_id,
                zone_number,
                reference.max_height,
                is_partial,
            )

            for corner in reference.corners:
                corner_helper.add_corner(
                    corner.position, corner.avg_height, reference_id
                )

        else:
            update_max_height(reference_id, reference.max_height)
            for corner in reference.corners:
                corner_helper.update_corner(
                    corner.position, corner.avg_height, reference_id
                )


def add_reference(
    col_position,
    row_position,
    product_id,
    zone,
    max_height: float = 0,
    is_partial: bool = False,
):
    reference = Reference(
        col_position, row_position, product_id, zone, max_height, is_partial
    )

    db_session.add(reference)

    db_session.commit()

    return reference.id


def update_max_height(id, max_height: float):
    refrence = Reference.query.get(id)

    refrence.max_height = max_height

    db_session.commit()


def get_reference(
    col_pos: int, row_pos: int, product_id: int, zone: int, is_partial: bool = False
) -> int:
    references = list(
        Reference.query.filter(
            (Reference.col_position == col_pos)
            & (Reference.row_position == row_pos)
            & (Reference.product_id == product_id)
            & (Reference.zone == zone)
            & (Reference.is_partial == is_partial)
        )
    )

    references_filtered = list(
        filter(
            lambda x: x.row_position == row_pos
            and x.col_position == col_pos
            and x.zone == zone
            and x.is_partial == is_partial
            and x.product_id == product_id,
            references,
        )
    )

    return references_filtered[0].id if len(references_filtered) > 0 else None


def get_references(product_id, is_partial: bool = False):
    references = Reference.query.filter(Reference.product_id == product_id).all()
    filtered_references = list(
        filter(
            lambda x: x.is_partial == is_partial and x.product_id == product_id,
            references,
        )
    )
    for reference in filtered_references:
        print("[DB] Returning references: ", reference.id)

    return filtered_references
