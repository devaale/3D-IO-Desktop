from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import marshmallow_dataclass

DEFAULT_ACCURACY = 0.0008
DEFAULT_DISTANCE_GROUND = 0.32
DEFAULT_DEPTH_FROM = 0.2715
DEFAULT_DEPTH_TO = 0.295
DEFAULT_DEPTH_FROM_2 = 0.2715
DEFAULT_DEPTH_TO_2 = 0.295
DEFAULT_CORNER_SIZE = 0.25
DEFAULT_VOXEL_DOWN = 0.0025
DEFAULT_MIN_POINTS_CLUSTER_DIVIDER = 18
DEFAULT_PRECENTAGE_OF_AVERAGE_POINTS_CLUSTER = 0.65
DEFAULT_CLUSTERING_THRESHOLD = 0.001
DEFAULT_CROP_PRECENTAGE_X = 1
DEFAULT_CROP_PRECENTAGE_Y = 1
DEFAULT_CROP_PRECENTAGE_Z = 1
DEFAULT_CROP_CENTER_PUSH_X = 0
DEFAULT_CROP_CENTER_PUSH_Y = 0
DEFAULT_CROP_CENTER_PUSH_Z = 0
DEFAULT_DETECTION_LINE_HEIGHT = 400
DEFAULT_DETECTION_LINE_THRESHOLD = 0.021
DEFAULT_DETECTION_LINE_PRECENTAGE = 0.25
DEFAULT_DETECTION_LINE_DELAY = 0.2
DEFAULT_FRAME_TO_USE = 0
DEFAULT_LIVE_VIEW = 0
DEFAULT_CAMERA_TO_VIEW = 0
DEFAULT_BOUND = 0
DEFAULT_VALIDATION_COUNT = 1
DEFAULT_VALIDATE = 0

DEFAULT_DICT = {
    "accuracy": DEFAULT_ACCURACY,
    "corner_size": DEFAULT_CORNER_SIZE,
    "distance_ground": DEFAULT_DISTANCE_GROUND,
    "depth_from": DEFAULT_DEPTH_FROM,
    "depth_to": DEFAULT_DEPTH_TO,
    "depth_from_2": DEFAULT_DEPTH_FROM_2,
    "depth_to_2": DEFAULT_DEPTH_TO_2,
    "live_view": DEFAULT_LIVE_VIEW,
    "camera_to_view": DEFAULT_CAMERA_TO_VIEW,
    "min_points_cluster_divider": DEFAULT_MIN_POINTS_CLUSTER_DIVIDER,
    "precentage_of_average_points_cluster": DEFAULT_PRECENTAGE_OF_AVERAGE_POINTS_CLUSTER,
    "voxel_down": DEFAULT_VOXEL_DOWN,
    "clustering_threshold": DEFAULT_CLUSTERING_THRESHOLD,
    "frame_to_use": DEFAULT_FRAME_TO_USE,
    "crop_precentage_x": DEFAULT_CROP_PRECENTAGE_X,
    "crop_precentage_y": DEFAULT_CROP_PRECENTAGE_Y,
    "crop_precentage_z": DEFAULT_CROP_PRECENTAGE_Z,
    "crop_center_push_x": DEFAULT_CROP_CENTER_PUSH_X,
    "crop_center_push_y": DEFAULT_CROP_CENTER_PUSH_Y,
    "crop_center_push_z": DEFAULT_CROP_CENTER_PUSH_Z,
}


class SettingType(Enum):
    COMMON = 10
    ADVANCED = 20
    PROCESSING = 30
    SPECIAL_CASE = 40


@dataclass
class SettingBase:
    name: str = ""
    label: str = ""
    toggle: bool = None
    type: int = SettingType.COMMON.value


@dataclass
class Setting(SettingBase):
    value: float = 0
    min_val: float = 0
    max_val: float = 0
    step: float = 0
    metric: str = ""
    val_mult: int = 1


def get_default_settings() -> List[Setting]:
    base_settings = [
        Setting(
            name="accuracy",
            label="Tikslumas",
            value=DEFAULT_ACCURACY,
            min_val=0.0005,
            max_val=0.005,
            step=0.00005,
            metric="mm",
            val_mult=1000,
        ),
        Setting(
            name="distance_ground",
            label="Kameros aukštis",
            value=DEFAULT_DISTANCE_GROUND,
            min_val=0.2,
            max_val=0.6,
            step=0.001,
            metric="cm",
            val_mult=100,
        ),
        Setting(
            name="depth_from",
            label="Min. Matomas gylis (Kamera 1)",
            value=DEFAULT_DEPTH_FROM,
            min_val=0.1,
            max_val=0.6,
            step=0.00025,
            metric="cm",
            val_mult=100,
        ),
        Setting(
            name="depth_to",
            label="Max. Matomas gylis (Kamera 1)",
            value=DEFAULT_DEPTH_TO,
            min_val=0.1,
            max_val=0.6,
            step=0.00025,
            metric="cm",
            val_mult=100,
        ),
        Setting(
            name="depth_from_2",
            label="Min. Matomas gylis (Kamera 2)",
            value=DEFAULT_DEPTH_FROM_2,
            min_val=0.2,
            max_val=0.6,
            step=0.00025,
            metric="cm",
            val_mult=100,
        ),
        Setting(
            name="depth_to_2",
            label="Max. Matomas gylis (Kamera 2)",
            value=DEFAULT_DEPTH_TO_2,
            min_val=0.2,
            max_val=0.6,
            step=0.00025,
            metric="cm",
            val_mult=100,
        ),
        Setting(
            name="corner_size",
            label="Kampo ROI dydis",
            value=DEFAULT_CORNER_SIZE,
            min_val=0,
            max_val=1,
            step=0.01,
            metric="%",
            val_mult=100,
        ),
        Setting(
            name="live_view",
            label="Kameros vaizdas",
            value=DEFAULT_LIVE_VIEW,
            min_val=0,
            max_val=1,
            step=1,
            metric="Rėžimas",
            val_mult=1,
        ),
        Setting(
            name="camera_to_view",
            label="Rodomos kameros pozicija",
            value=DEFAULT_CAMERA_TO_VIEW,
            min_val=0,
            max_val=1,
            step=1,
            metric="Pozicija",
            val_mult=1,
        ),
        Setting(
            name="depth_bound_1",
            label="Gylio pjūvio vertė (Kamera 1)",
            value=DEFAULT_BOUND,
            min_val=0,
            max_val=0.01,
            step=0.0005,
            metric="mm",
            val_mult=1000,
        ),
        Setting(
            name="depth_bound_2",
            label="Gylio pjūvio vertė (Kamera 2)",
            value=DEFAULT_BOUND,
            min_val=0,
            max_val=0.01,
            step=0.0005,
            metric="mm",
            val_mult=1000,
        ),
    ]

    advanced_settings = [
        Setting(
            name="voxel_down",
            label="Vokseliavimas",
            value=DEFAULT_VOXEL_DOWN,
            toggle=True,
            min_val=0,
            max_val=0.1,
            step=0.00005,
            type=SettingType.ADVANCED.value,
        ),
        Setting(
            name="clustering_threshold",
            label="Klasterizavimo atstumas",
            value=DEFAULT_CLUSTERING_THRESHOLD,
            min_val=0,
            max_val=0.5,
            step=0.001,
            type=SettingType.ADVANCED.value,
            metric="mm",
            val_mult=1000,
        ),
        Setting(
            name="frame_to_use",
            label="Kadras buferyje",
            value=DEFAULT_FRAME_TO_USE,
            toggle=True,
            min_val=0,
            max_val=30,
            step=1,
            type=SettingType.ADVANCED.value,
        ),
        Setting(
            name="min_points_cluster_divider",
            label="Min. taškų klasteryje daliklis",
            value=DEFAULT_MIN_POINTS_CLUSTER_DIVIDER,
            toggle=True,
            min_val=0,
            max_val=30,
            step=1,
            type=SettingType.ADVANCED.value,
        ),
        Setting(
            name="precentage_of_average_points_cluster",
            label="Min. taškų klasteryje % nuo pradinės vertės",
            value=DEFAULT_PRECENTAGE_OF_AVERAGE_POINTS_CLUSTER,
            toggle=True,
            min_val=0.1,
            max_val=1,
            step=0.01,
            metric="%",
            val_mult=100,
            type=SettingType.ADVANCED.value,
        ),
        Setting(
            name="validation_count",
            label="Validacijos kiekis",
            value=DEFAULT_VALIDATION_COUNT,
            toggle=True,
            min_val=0,
            max_val=100,
            step=1,
            metric="",
            val_mult=1,
            type=SettingType.ADVANCED.value,
        ),
        Setting(
            name="validate",
            label="Validacija",
            value=DEFAULT_VALIDATE,
            toggle=True,
            min_val=0,
            max_val=1,
            step=1,
            metric="RĖŽIMAS",
            val_mult=1,
            type=SettingType.ADVANCED.value,
        ),
    ]

    processing_settings = [
        Setting(
            name="crop_precentage_x",
            label="Kirpimas x %",
            value=DEFAULT_CROP_PRECENTAGE_X,
            toggle=False,
            min_val=0,
            max_val=1,
            step=0.01,
            metric="%",
            val_mult=100,
            type=SettingType.PROCESSING.value,
        ),
        Setting(
            name="crop_precentage_y",
            label="Kirpimas y %",
            value=DEFAULT_CROP_PRECENTAGE_Y,
            toggle=False,
            min_val=0,
            max_val=1,
            step=0.01,
            metric="%",
            val_mult=100,
            type=SettingType.PROCESSING.value,
        ),
        Setting(
            name="crop_precentage_z",
            label="Kirpimas z %",
            value=DEFAULT_CROP_PRECENTAGE_Z,
            toggle=False,
            min_val=0,
            max_val=2,
            step=0.01,
            metric="%",
            val_mult=100,
            type=SettingType.PROCESSING.value,
        ),
        Setting(
            name="crop_center_push_x",
            label="Kirpimo postumis x",
            value=DEFAULT_CROP_CENTER_PUSH_X,
            toggle=False,
            min_val=-1,
            max_val=1,
            step=0.001,
            metric="",
            val_mult=1,
            type=SettingType.PROCESSING.value,
        ),
        Setting(
            name="crop_center_push_y",
            label="Kirpimo postumis y",
            value=DEFAULT_CROP_CENTER_PUSH_Y,
            toggle=False,
            min_val=-1,
            max_val=1,
            step=0.001,
            metric="",
            val_mult=1,
            type=SettingType.PROCESSING.value,
        ),
        Setting(
            name="crop_center_push_z",
            label="Kirpimas postumis z",
            value=DEFAULT_CROP_CENTER_PUSH_Z,
            toggle=False,
            min_val=-1,
            max_val=1,
            step=0.001,
            metric="",
            val_mult=1,
            type=SettingType.PROCESSING.value,
        ),
    ]

    return base_settings + advanced_settings + processing_settings


@dataclass
class Settings:
    settings: List[Setting] = field(default_factory=get_default_settings)


def update_settings_from_dict(settings_schema, settings_dict: {}):
    for setting in settings_schema[0]["settings"]:
        for (key, value) in settings_dict.items():
            if setting["name"] == key:
                setting["value"] = value


def get_settings_dict_from_schema(settings_schema) -> {}:
    settings_dict = {}
    for setting in settings_schema:
        settings_dict[setting["name"]] = setting["value"]

    return settings_dict


def default_settings():
    settings_schema = marshmallow_dataclass.class_schema(Settings)()
    settings_config = settings_schema.dump(Settings)
    return [settings_config]
