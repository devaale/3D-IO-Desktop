import cv2
import numpy as np

class VisualizerRGB:
    
    @classmethod
    def render(self, frames):
        if frames is None:
            return
        
        color_image = np.asanyarray(frames.get_data())
        cv2.namedWindow("RGB Camera", cv2.WINDOW_AUTOSIZE)
        cv2.imshow("RGB Camera", color_image)
        cv2.waitKey(1)
        