class SelectedProduct(object):
    def __init__(self, id, model, row_count, col_count, has_ref=True):
        self.id = id
        self.model = model
        self.has_ref = has_ref
        self.row_count = row_count
        self.col_count = col_count
        
        self.corners = []
        self.average_height = 0