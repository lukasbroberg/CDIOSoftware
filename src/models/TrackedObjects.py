from utils.getDistance import *

class TrackedObject:
    def __init__(self, id, x, y, is_orange=False):
        self.id = id
        self.x = x
        self.y = y
        self.isOrange = is_orange

class ObjectTracker:
    def __init__(self, max_distance=50):
        self.tracked = {}       # id -> TrackedObject
        self.next_id = 0
        self.max_distance = max_distance  # max px to still be same object

    def update(self, detections):
        updated = {}
    

        for det in detections:
            best_id = None
            best_dist = float("inf")

            # Match detection to nearest existing tracked object
            for tid, obj in self.tracked.items():
                if obj.isOrange != det.isOrange:
                    continue  # don't match across types
                dist = getDistance(det.x, det.y, obj.x, obj.y,0,0)
                if dist < best_dist and dist < self.max_distance:
                    best_dist = dist
                    best_id = tid

            if best_id is not None:
                # Update existing
                self.tracked[best_id].x = det.x
                self.tracked[best_id].y = det.y
                updated[best_id] = self.tracked[best_id]
            else:
                # New object
                new_obj = TrackedObject(self.next_id, det.x, det.y, det.isOrange)
                updated[self.next_id] = new_obj
                self.next_id += 1

        self.tracked = updated
        return list(self.tracked.values())