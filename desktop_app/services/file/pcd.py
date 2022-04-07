import open3d as o3d
from desktop_app.errors.file import FileReadError, FileWriteError
from desktop_app.services.file.base import FileService


class PCDFileService(FileService):
    @classmethod
    def write(self, path: str, cloud: o3d.geometry.PointCloud):
        try:
            o3d.io.write_point_cloud(path, cloud)
        except Exception as error:
            raise FileWriteError(
                f"point cloud, path: {path} | reason: {error}"
            ) from error

    @classmethod
    def read(self, path: str) -> o3d.geometry.PointCloud:
        try:
            cloud = o3d.io.read_point_cloud(path)
            return cloud
        except Exception as error:
            raise FileReadError(
                f"point cloud, path: {path} | reason: {error}"
            ) from error
