ROBOTCONFIG = {
    'angleTolerance': 10,        # degrees - An acceptabel range of degrees of error for the robot, to move towards the target
    'closeRangeTolerance': 15,  # degrees - An acceptabel range of degrees of error for the robot close target
    'distanceTolerance': 100,   # px — "close enough to goal" for RELEASE
    'collectOffset': 60,        # px — stop MoveToBall here, then COLLECT + ram forward
    'leastDistanceToBall': 20, # px - from which targets least amount of distance
    'backupDistance': 150,      # px — reverse this far after collecting
    'dropOffOffset': 170,        
    'bounadryOffset': 50,       # px - boundary's buffer 
    'fullTurnTime': 6.48,
    'goalDropOffOffset': 450,
    'goalAlignZoneOffset': 100,
    'targetOffsetX': -20, 
    'targetOffsetY': -20,
    'maxDistToBoundary': 100,
}