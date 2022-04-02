import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from ..config import BaseConfig

engine = create_engine(
    BaseConfig.SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    from ..models import (
        product,
        reference,
        corner,
        plc,
        plc_block,
        result,
        zone_reference,
        global_settings,
    )

    Base.metadata.create_all(bind=engine)


def populate_default_db():
    populate_default_global_settings()
    populate_default_plc()
    populate_default_products()


def populate_default_global_settings():
    from ..models.global_settings import GlobalSettings

    if GlobalSettings.query.first() is None:
        global_settings = GlobalSettings(
            file_service_time_days=10, camera_one_serial="115222070766"
        )
        db_session.bulk_save_objects([global_settings])
        db_session.commit()


def populate_default_products():
    from ..models.product import Product
    from ..models.enums.product import ProductType, ProcessingStrategy

    if Product.query.first() is None:
        products = [
            Product(
                model="FMB110",
                row_count=1,
                col_count=3,
                camera_1_rows=1,
                camera_2_rows=1,
                product_type=ProductType.FMB110.value,
                processing_type=ProcessingStrategy.CLUSTERING.value,
            ),
            # Product(
            #     model="FMB120",
            #     row_count=6,
            #     col_count=3,
            #     camera_1_rows=3,
            #     camera_2_rows=3,
            #     product_type=ProductType.FMB120.value,
            #     processing_type=ProcessingStrategy.CLUSTERING.value,
            # ),
            # Product(
            #     model="FMB130",
            #     row_count=6,
            #     col_count=3,
            #     camera_1_rows=3,
            #     camera_2_rows=3,
            #     product_type=ProductType.FMB130.value,
            #     processing_type=ProcessingStrategy.CLUSTERING.value,
            # ),
            # Product(
            #     model="FMB140",
            #     row_count=6,
            #     col_count=3,
            #     camera_1_rows=3,
            #     camera_2_rows=3,
            #     product_type=ProductType.FMB140.value,
            #     processing_type=ProcessingStrategy.CLUSTERING.value,
            # ),
            # Product(
            #     model="FMB150",
            #     row_count=6,
            #     col_count=3,
            #     camera_1_rows=3,
            #     camera_2_rows=3,
            #     product_type=ProductType.FMB150.value,
            #     processing_type=ProcessingStrategy.CLUSTERING.value,
            # ),
            Product(
                model="FMB010",
                row_count=6,
                col_count=3,
                camera_1_rows=3,
                camera_2_rows=3,
                product_type=ProductType.FMB010.value,
                processing_type=ProcessingStrategy.CLUSTERING.value,
            ),
            Product(
                model="FMB920",
                row_count=6,
                col_count=3,
                camera_1_rows=3,
                camera_2_rows=3,
                product_type=ProductType.FMB920.value,
                processing_type=ProcessingStrategy.CLUSTERING.value,
            ),
            Product(
                model="FMB600",
                row_count=3,
                col_count=3,
                camera_1_rows=2,
                camera_2_rows=1,
                product_type=ProductType.FMB600.value,
            ),
        ]
        db_session.bulk_save_objects(products)
        db_session.commit()


def populate_default_plc():
    from ..models.plc import Plc
    from ..models.plc_block import PlcBlock
    from ..models.enums.plc_block import PLCDataType, PLCCommandType

    if Plc.query.first() is None:
        plc = Plc("10.50.46.10", 0, 0)
        db_session.add(plc)
        db_session.commit()
        plc_blocks = [
            PlcBlock(
                "Life bit",
                None,
                0,
                0,
                PLCDataType.BOOL,
                PLCCommandType.LIFE_BIT,
                1,
                plc.id,
            ),
            PlcBlock(
                "Trigger Flag ACK",
                None,
                0,
                1,
                PLCDataType.BOOL,
                PLCCommandType.TRIGGER_FLAG_ACK,
                1,
                plc.id,
            ),
            PlcBlock(
                "Product Type ACK",
                None,
                2,
                0,
                PLCDataType.INT,
                PLCCommandType.PRODUCT_TYPE_ACK,
                1,
                plc.id,
            ),
            PlcBlock(
                "Scan done",
                None,
                4,
                0,
                PLCDataType.BOOL,
                PLCCommandType.SCAN_DONE,
                1,
                plc.id,
            ),
            PlcBlock(
                "Learning mode ACK",
                None,
                4,
                1,
                PLCDataType.BOOL,
                PLCCommandType.LEARNING_MODE_ACK,
                1,
                plc.id,
            ),
            PlcBlock(
                "Template exist",
                None,
                4,
                2,
                PLCDataType.BOOL,
                PLCCommandType.TEMPLATE_EXIST,
                1,
                plc.id,
            ),
            PlcBlock(
                "Result", None, 6, 0, PLCDataType.BOOL, PLCCommandType.RESULT, 1, plc.id
            ),
            PlcBlock(
                "Product type",
                None,
                10,
                0,
                PLCDataType.INT,
                PLCCommandType.PRODUCT_TYPE,
                1,
                plc.id,
            ),
            PlcBlock(
                "Trigger flag",
                None,
                12,
                0,
                PLCDataType.BOOL,
                PLCCommandType.TRIGGER_FLAG,
                1,
                plc.id,
            ),
            PlcBlock(
                "Learning mode enable",
                None,
                12,
                1,
                PLCDataType.BOOL,
                PLCCommandType.LEARNING_MODE_ENABLE,
                1,
                plc.id,
            ),
        ]
        db_session.bulk_save_objects(plc_blocks)
        db_session.commit()
