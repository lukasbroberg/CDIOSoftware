ROBOTCONFIG = {
    'angleTolerance': 5.0,        # degrees - An acceptabel range of degrees of error for the robot, to move towards the target
    'closeRangeTolerance': 10.0,  # degrees - An acceptabel range of degrees of error for the robot close target
    'distanceTolerance': 100,   # px — "close enough to goal" for RELEASE
    'collectOffset': 12.0,        # cm — stop MoveToBall here, then COLLECT + ram forward
    'waypointOffset': 17.0,
    'waypointArrivalTolerance': 5.0,  # cm — do not cut corners around cross
    # Ground distance in cm.  Ignore detections inside the robot footprint;
    # these are usually balls falsely detected on the robot itself.
    'minimumTargetDistance': 25.0,
    # Ignore balls that are inside/too close to the middle cross.  They are
    # unsafe to collect and often make the robot fight the obstacle.
    'crossBallIgnoreRadius': 34.0,  # cm
    # Balls close to the wall are collected from an approach point inside the
    # field, and with a shorter final nudge, so the robot does not ram the edge.
    'edgeBallSafetyMargin': 18.0,   # cm from wall before we treat it as risky
    'edgeBallApproachMargin': 32.0, # cm from wall for the safe approach point
    'edgeCollectForward': 1.0,      # cm cautious nudge during pickup near edge
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
