# collvoid
ROS multi_robot_collision_avoidance

Visit http://wiki.ros.org/multi_robot_collision_avoidance

# Instructions to run the simulator

1 Launch the simulator by 
`roslaunch collvoid_stage stage_sim.launch`

2 Launch collision avoidance nodes for 10 robots
`roslaunch collvoid_stage 1to10.launch`

3 Publish the goal 
`rostopic pub /robot_0/move_base_simple/goal geometry_msgs/PoseStamped "header:
  seq: 0
  stamp:
    secs: 0
    nsecs: 0
  frame_id: 'map'
pose:
  position:
    x: 10.0
    y: 40.0
    z: 0.0
  orientation:
    x: 0.0
    y: 0.0
    z: 0.0
    w: 1.0" 
`