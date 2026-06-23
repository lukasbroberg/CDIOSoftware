class Cross:
    def __init__(self, x, y, length_cm= 20, arm_width_cm =3, height_cm=3):
        self.x = x
        self.y = y
        self.length_cm = length_cm
        self.arm_width_cm = arm_width_cm
        self.height_cm = height_cm

    def to_point(self):
        return {"x": self.x, "y": self.y}
    