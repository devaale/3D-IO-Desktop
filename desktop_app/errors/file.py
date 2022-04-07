class FileReadError(Exception):
    def __init__(self, message):
        self.message = "Failed to read " + message
        super().__init__(self.message)


class FileWriteError(Exception):
    def __init__(self, message):
        self.message = "Failed to read " + message
        super().__init__(self.message)
