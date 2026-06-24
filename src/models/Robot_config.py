ROBOTCONFIG = {
    'angleTolerance': 5.0,        # degrees - An acceptabel range of degrees of error for the robot, to move towards the target
    'closeRangeTolerance': 15.0,  # degrees - An acceptabel range of degrees of error for the robot close target
    'distanceTolerance': 100,   # px — "close enough to goal" for RELEASE
    'collectOffset': 12.0,        # cm — stop MoveToBall here, then COLLECT + ram forward
    'waypointOffset': 17.0,
    # Ground distance in cm.  Ignore detections inside the robot footprint;
    # these are usually balls falsely detected on the robot itself.
    'minimumTargetDistance': 25.0,
    'backupDistance': 2.0,      # px — reverse this far after collecting
    'bounadryOffset': 50,       # px - boundary's buffer 
    'fullTurnTime': 6.48,
    'goalDropOffOffset': 200.0, # px
    'goalAlignZoneOffset': 100.0,
    'targetOffsetX': -20, 
    'targetOffsetY': -20,
    'maxDistToBoundary': 25.0,
    'maxDriveDist': 4.0,
}
