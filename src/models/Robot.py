class Robot:
    #Constructor for Robot
    def __init__(self,x1,y1,x2,y2,rotation,state):
        self.collision = {
            x1,
            y1,
            x2,
            y2,
        }
        self.rotation = rotation
        self.state = state
    
    