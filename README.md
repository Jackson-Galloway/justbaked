# justbaked
Arkansas State University IEEE Robotics Team for the 2025 region 5 conference in Whichita Kansas

Team Members
- Chase Himschoot
- Jackson Galloway
- Jaiden Strong
- Josh Featherston

Robot Purpose
  The robot is intended to be a "fire fighting robot". The competition rules outline an arena in which there are dowels placed vertically in the arena to serve as trees. The robot must successfully navigate these trees to locate the fire and then return to the starting position. After this has been done the robot must    them continue to latch a "hose" which is just rope and deliver it to the fire. All of this must be done autonomously without assistance from a person.

How it is done
  The robot will use ROS2 Jazzy in order to utilize SLAM and NAV2 to correlate sensor data into the controller to find the fire. 

Required Packages
  -- ROS2 Control
  -- ROS2 Controllers
  -- Slam_Tech SLAM_TOOLBOX
  -- NAV2
  -- Joint_State_Publisher

File Structure  
justbaked/  
├── src/                        ← source code  
  ├── robot_bringup             ← robot startup  
  ├── sllidar_ros2              ← 2D lidar data interpretation  
  ├── temp_sens                 ← temperature sensing  
  ├── turtlebot4_description    ← joint publishing information for simulation  
  └── turtlebot4_navigation     ← navigation and slam parameters/launch files  
├── pictures/                   ← images, design docs, screenshots  
├── README.md  
└── LICENSE  

Startup Procedure

1. First after cloning the github repository, colcon build in the justbaked/justbaked directory. You may have to do colcon build --symlink-install if you have problems building initially.  
2. After building, you need to navigate to the justbaked/justbaked directory and source install/setup.bash in order to source your ROS2 workspace.  
3. Once sourced, if you are running this on a linux machine that is using ssh or remote desktop you can choose to launch the startup file or the button press file.  
4. If you choose to launch with the startup file, it launches with RVIZ 2 where you can set goals in RVIZ2 that the robot will then navigate to. This is done by typing ros2 launch robot_bringup startup.launch.py  
5. If you choose to launch with the button press file, it reads pre-determined waypoints in the round launch files and then navigates to those points based on the points found in the waypoints files. Currently Round 2 is very buggy and Round 3 does not work properly but Round 1 works very well. This is done by typing ros2 run robot_bringup button_publisher.py  
