class CameraError(Exception):
    def __init__(self, message):
        self.message = "Camera error has occurred: " + message
        super().__init__(self.message)
