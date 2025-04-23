<!-- Badges -->
![License](https://img.shields.io/github/license/Jackson-Galloway/justbaked)
![Issues](https://img.shields.io/github/issues-raw/Jackson-Galloway/justbaked)

# 🔥 justbaked 🔥  
<mark>Arkansas State University IEEE Robotics Team for the 2025 Region 5 Conference in Wichita, Kansas</mark>

<details open>
<summary>🚀 Quick Overview</summary>

We’re building an **autonomous firefighting robot** that navigates a “forest” of dowels, finds the fire, latches its hose (rope), and returns—completely on its own.

</details>

---

## 🧑‍🤝‍🧑 Team Members  
- Chase Himschoot  
- Jackson Galloway  
- Jaiden Strong  
- Josh Featherston  

---

## 🤖 Robot Purpose  
The robot must:

1. **SLAM & Navigate** around vertical dowels (“trees”)  
2. **Locate the fire** (heat source)  
3. **Return to start**, latch hose (rope)  
4. **Deliver the hose** back to the fire  

_All fully autonomous—no human intervention._

---

## 📸 Gallery

<p align="center">
  <img src="pictures/Jackson/Robot.jpg" alt="Finished Robot" width="600" />
</p>

<p align="center">
  <video
    src="https://raw.githubusercontent.com/Jackson-Galloway/justbaked/main/pictures/Jackson/Round1.mp4"
    width="600"
    controls
    autoplay
    loop
    muted
  >
    Your browser does not support the video tag.
  </video>
</p>

---

## 🔧 How It Works  
We leverage **ROS 2 Jazzy**, SLAM ToolBox, and Nav2:

- ROS2 Control  
- ROS2 Controllers  
- Slam_Tech SLAM_TOOLBOX  
- NAV2  
- Joint_State_Publisher  

---

## 📁 File Structure
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
