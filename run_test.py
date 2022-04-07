class CameraError(Exception):
    def __init__(self, message):
        self.message = "Camera error has occurred: " + message
        super().__init__(self.message)


def function_that_fails():
    try:
        val = 4 / 0
    except Exception as error:
        raise CameraError("Random") from error


if __name__ == "__main__":
    try:
        function_that_fails()
    except CameraError as error:
        print(error)
