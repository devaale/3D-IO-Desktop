import os
import json
import copy
from typing import *

from ...helpers import settings_helper

DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_DIR = os.path.join(DIR, "presets/")

FILE_APPENDINX = "_processing_preset"
FILE_EXTENSION = ".json"


def save_settings_to_file(settings: {}, product_model: str):
    path = full_path(product_model)
    with open(path, "w") as file:
        json.dump(settings, file)

        file.close()


def settings_file_exist(full_path: str) -> bool:
    return True if os.path.isfile(full_path) else False


def read_settings(product_model: str):
    path = full_path(product_model)

    if not settings_file_exist(path):
        print("Settings file doesn't exist, path:", path)
        create_settings_file(path)

    return read_settings_from_file(path)


def read_settings_from_file(full_path: str):
    with open(full_path, "r") as file:
        content = json.load(file)

        file.close()

    return content


def get_default_settings() -> dict:
    return settings_helper.DEFAULT_DICT


def create_settings_file(path: str):
    with open(path, "w") as outfile:
        json.dump(settings_helper.DEFAULT_DICT, outfile)


def full_path(product_model: str) -> str:
    return PRESETS_DIR + product_model + FILE_APPENDINX + FILE_EXTENSION
