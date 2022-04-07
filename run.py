manager = None
plc_adapter = None

sensor_trigger_event = None
processing_done_event = None

laser_sensor = None
camera_service = None
camera_service_thread = None

processing_service = None
plc_service = None
plc_service_thread = None
plc_conn_service = None

file_service = None


def set_plc_service(on: bool):
    start_plc_service() if on else stop_plc_service()


def start_plc_service():
    global plc_service, plc_service_thread
    if plc_service_thread is None:
        plc_service_thread = Thread(target=plc_service.run)
        plc_service_thread.setDaemon(True)
        plc_service_thread.start()
    else:
        logger.info("PLC Service already started...")


def stop_plc_service():
    global plc_service, plc_service_thread
    if plc_service_thread is not None:
        plc_service.stop()
        plc_service_thread.join()
        plc_service_thread = None
    else:
        logger.info("PLC Service is not started...")


def set_camera_service(on: bool):
    start_camera_service() if on else stop_camera_service()


def start_camera_service():
    global camera_service, camera_service_thread
    if camera_service_thread is None:
        camera_service_thread = Thread(target=camera_service.run)
        camera_service_thread.setDaemon(True)
        camera_service_thread.start()
    else:
        logger.info("Camera service already started...")


def stop_camera_service():
    global camera_service, camera_service_thread
    if camera_service_thread is not None:
        # stop_laser_sensor()
        camera_service.stop()
        camera_service_thread.join()
        camera_service_thread = None


def start_file_service():
    global file_service
    global_settings = global_settings_helper.get()
    file_service.start(int(global_settings.file_service_time_days))


def stop_file_service():
    global file_service
    if file_service is not None:
        file_service.stop()


def update_camera_settings(product_model):
    product = product_helper.get_product_by_model(product_model)
    processing_service.product(product)


def manual_validation():
    camera_service.set_manual_validation()


def manual_reference():
    camera_service.set_manual_reference()


def manual_detect():
    camera_service.set_manual_detect()


def init_database():
    init_db()
    populate_default_db()


def run_gui():
    products = product_helper.get_products_names()

    app = MainApp(
        products,
        set_plc_service,
        set_camera_service,
        update_camera_settings,
        manual_reference,
        manual_detect,
    )

    app.run()


def exit():
    stop_plc_service()
    stop_camera_service()
    stop_file_service()


if __name__ == "__main__":
    import atexit
    from threading import Thread
    from multiprocessing import Manager, freeze_support
    from threading import Event
    from desktop_app.services.plc.connection_service import PlcConnectionService

    from desktop_app.services.camera.service import CameraService
    from desktop_app.common.plc_adapter import PlcAdapter
    from desktop_app.common.logger import logger
    from desktop_app.common.file_service import FileService
    from desktop_app.helpers import global_settings_helper
    from desktop_app.helpers import product_helper
    from desktop_app.app.database import init_db, populate_default_db
    from desktop_app.gui.main_window import MainApp
    from desktop_app.services.processing.service import ProcessingService

    freeze_support()
    atexit.register(exit)

    manager = Manager()
    plc_adapter = PlcAdapter()

    sensor_trigger_event = Event()
    processing_done_event = Event()
    plc_start_event = Event()

    plc_conn_service = PlcConnectionService(plc_adapter=plc_adapter)

    proc_service = ProcessingService()
    camera_service = CameraService(
        sensor_trigger_event=sensor_trigger_event, proc_service=processing_service
    )
    file_service = FileService()

    init_database()
    start_file_service()
    run_gui()
