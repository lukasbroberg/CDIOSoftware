ROBOTCONFIG = {
    'angleTolerance': 10.0,        # degrees - An acceptabel range of degrees of error for the robot, to move towards the target
    'closeRangeTolerance': 15.0,  # degrees - An acceptabel range of degrees of error for the robot close target
    'distanceTolerance': 100,   # px — "close enough to goal" for RELEASE
    'collectOffset': 20.0,        # cm — stop MoveToBall here, then COLLECT + ram forward
    'leastDistanceToBall': 30.0, # px - from which targets least amount of distance
    'backupDistance': 2.0,      # px — reverse this far after collecting
    'dropOffOffset': 170,        
    'bounadryOffset': 50,       # px - boundary's buffer 
    'fullTurnTime': 6.48,
    'goalDropOffOffset': 30.0,
    'goalAlignZoneOffset': 100.0,
    'targetOffsetX': -20, 
    'targetOffsetY': -20,
    'maxDistToBoundary': 25.0,
}