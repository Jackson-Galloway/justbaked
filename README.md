# ASUIEEE25
Arkansas State University IEEE Robotics Team for the 2025 region 5 conference in Whichita Kansas

Team Members
- Chase Himschoot
- Jackson Galloway
- Jaiden Strong
- Josh Featherston

Robot Purpose
  The robot is intended to be a "fire fighting robot". The competition rules outline an arena in which there are dowels placed vertically in the arena to serve as trees. The robot must successfully navigate these trees to locate the fire and then return to the starting position. After this has been done the robot must    them continue to latch a "hose" which is just rope and deliver it to the fire. All of this must be done autonomously without assistance from a person.

How it is done
  The robot will use ROS2 Jazzy in order to utilize SLAM and correlate sensor data into the controller to find the fire. 

Required Packages
  -- ROS2 Control
  -- ROS2 Controllers
  -- Slam_Tech SLAM_TOOLBOX
  -- NAV2
  -- Joint_State_Publisher

File Structure
ASUIEEE25/
├── src/             ← source code
├── docs/            ← images, design docs, screenshots
├── examples/        ← sample usage
├── scripts/         ← build/deploy scripts
├── .github/         ← CI workflows, templates
├── README.md
└── LICENSE
