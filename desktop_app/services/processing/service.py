from threading import Lock
from desktop_app.models.product import Product
from desktop_app.services.camera.settings_proxy import SettingsProxy
from desktop_app.services.file.json import JSONFileService
from desktop_app.services.file.pcd import PCDFileService
from desktop_app.services.processing import functions
import open3d as o3d


class ProcessingService:
    FILE_PATH = "C:/Users/evald/Documents/Coding/Projects/University/3D-IO-Desktop/desktop_app/services/settings/presets/FMB110_processing_preset.json"
    PCD_FILE_PATH = "C:/Users/evald/Documents/Coding/Projects/University/3D-IO-Desktop/desktop_app/data/original_cloud_2_0_2022-04-05__7_23_38_397026.pcd"

    def __init__(self):
        self._lock = Lock()

        self.detect = False
        self._models = None
        self._curr_product = None

        self._settings = SettingsProxy()
        self._pcd_service = PCDFileService()

    @property
    def product(self) -> Product:
        with self._lock:
            return self._curr_product

    # TODO: Change ORM to SQL model and fetch data as product.models
    # TODO: Set settings service - use JSONFileService to read data
    # TODO: Or add web settings and access settings via self._curr_product.settings
    @product.setter
    def product(self, product: Product):
        with self._lock:
            self._curr_product = product
            self._models = functions.get_references(self._curr_product.id)
            self._settings.load(JSONFileService().read(self.FILE_PATH))
            self._detect = self._curr_product.has_reference

            print(f"Updated product to: {self._curr_product.model}")
            print(f"Model count: {len(self._models)}")
            print(f"Settings value: {self._settings.get('depth_from')}")
            print(f"Detect: {self._detect}")

    def process(self, frames, camera_intrinsics):
        with self._lock:
            cloud = o3d.geometry.PointCloud()
            # for frame in frames:
            #     cloud += functions.process_cloud(
            #         camera_intrinsics, frame, self._settings
            #     )

            cloud = PCDFileService().read(self.PCD_FILE_PATH)

            cloud_post = functions.remove_points(cloud, self._settings.get("depth_to"))

            cloud_preproc = functions.process_cloud_test(cloud_post, self._settings)

            o3d.visualization.draw_geometries([cloud_preproc])
