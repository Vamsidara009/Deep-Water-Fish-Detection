import cv2
import numpy as np

def enhance_frame(frame):
    """
    Applies CLAHE and White Balance as per the Deep-Sea Fish Detection report.
    """
    # 1. CLAHE in LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    enhanced_lab = cv2.merge([l_eq, a, b])
    
    bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # 2. Grey World White Balance Correction
    b_ch, g_ch, r_ch = cv2.split(bgr.astype(np.float32))
    
    # Avoid division by zero by adding a small epsilon
    b_mean = b_ch.mean() + 1e-6
    g_mean = g_ch.mean() + 1e-6
    r_mean = r_ch.mean() + 1e-6
    
    avg = (b_mean + g_mean + r_mean) / 3
    
    b_ch = np.clip(b_ch * (avg / b_mean), 0, 255)
    g_ch = np.clip(g_ch * (avg / g_mean), 0, 255)
    r_ch = np.clip(r_ch * (avg / r_mean), 0, 255)
    
    # Merge and return enhanced frame
    return cv2.merge([b_ch, g_ch, r_ch]).astype(np.uint8)


def draw_ui(frame, count, count_line):
    """
    Draws the counting line and current count on the frame.
    """
    # Draw horizontal counting line
    cv2.line(frame, (0, count_line), (frame.shape[1], count_line), (0, 0, 255), 2)
    
    # Text overlay background for better visibility
    cv2.rectangle(frame, (10, 10), (300, 60), (0, 0, 0), -1)
    
    # Display the count
    cv2.putText(frame, f"Total Count: {count}", (20, 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return frame

from scipy.spatial import distance

class CentroidTracker:
    def __init__(self, max_disappeared=30, max_distance=100):
        self.next_obj_id = 0
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, rects):
        if len(rects) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    del self.objects[obj_id]
                    del self.disappeared[obj_id]
            return {}

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for i, (startX, startY, endX, endY) in enumerate(rects):
            input_centroids[i] = (int((startX + endX) / 2.0), int((startY + endY) / 2.0))

        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.objects[self.next_obj_id] = input_centroids[i]
                self.disappeared[self.next_obj_id] = 0
                self.next_obj_id += 1
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            D = distance.cdist(np.array(object_centroids), input_centroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > self.max_distance:
                    continue

                obj_id = object_ids[row]
                self.objects[obj_id] = input_centroids[col]
                self.disappeared[obj_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            for row in unused_rows:
                obj_id = object_ids[row]
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    del self.objects[obj_id]
                    del self.disappeared[obj_id]

            for col in unused_cols:
                self.objects[self.next_obj_id] = input_centroids[col]
                self.disappeared[self.next_obj_id] = 0
                self.next_obj_id += 1

        rect_to_id = {}
        for obj_id, centroid in self.objects.items():
            for i, c in enumerate(input_centroids):
                if c[0] == centroid[0] and c[1] == centroid[1] and self.disappeared[obj_id] == 0:
                    rect_to_id[i] = obj_id
                    break
                    
        return rect_to_id
