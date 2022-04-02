class BoundingBox(object):
    def __init__(self, min_bound: [], max_bound: [], corner_points: []):
        self.min_x = min_bound[0]
        self.min_y = min_bound[1]
        self.min_z = min_bound[2]

        self.max_x = max_bound[0]
        self.max_y = max_bound[1]
        self.max_z = max_bound[2]

        self.corner_points = corner_points







