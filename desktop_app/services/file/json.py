import json
from desktop_app.errors.file import FileReadError, FileWriteError
from desktop_app.services.file.base import FileService


class JSONFileService(FileService):
    def write(self, path: str):
        pass

    @classmethod
    def read(self, path: str) -> str:
        json_dict = {}
        try:
            with open(path) as file:
                for key, value in json.load(file).items():
                    json_dict[key] = value

            return str(json_dict).replace("'", '"')
        except Exception as error:
            raise FileReadError(f"json, path: {path} | reason: {error}") from error
