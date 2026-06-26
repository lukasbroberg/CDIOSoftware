class Ball:
    #Constructor
    def __init__(self, x, y, isOrange):
        self.x = x
        self.y = y
        self.isOrange = isOrange
    
    def _repr_(self):
        color = "Orange" if self.isOrange else "White"
        return f"Ball({color}, position=({self.position['x']}, {self.position['y']}), size={self.size})"