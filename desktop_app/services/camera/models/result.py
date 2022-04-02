class Result(object):
    def __init__(
        self, scan_number: int, datetime, product_id: int, reference: bool = False
    ):
        self.scan_number = scan_number
        self.datetime = datetime
        self.product_id = product_id
        self.reference = True
