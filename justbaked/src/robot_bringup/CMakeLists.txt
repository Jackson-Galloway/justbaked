cmake_minimum_required(VERSION 3.5)
project(robot_bringup)

# Default standards
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(yaml-cpp REQUIRED)

# Build C++ executable for waypoint navigation
add_executable(waypoint_nav_cpp src/waypoint_nav.cpp)
ament_target_dependencies(waypoint_nav_cpp
  rclcpp
  std_msgs
  geometry_msgs
  nav2_msgs
  tf2
  tf2_geometry_msgs
)

# Build C++ executable for determine_fire_location
add_executable(determine_fire_location src/determine_fire_location.cpp)
ament_target_dependencies(determine_fire_location
  rclcpp
  std_msgs
)

# Link the necessary libraries for each executable
target_link_libraries(waypoint_nav_cpp yaml-cpp)
target_link_libraries(determine_fire_location yaml-cpp)

# Install compiled binaries
install(TARGETS waypoint_nav_cpp
  DESTINATION lib/${PROJECT_NAME}
)
install(TARGETS determine_fire_location
  DESTINATION lib/${PROJECT_NAME}
)

# Install Python scripts
install(PROGRAMS
  catapult/catapult_launch.py	
  rounds/button_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch and resource directories
install(DIRECTORY
  launch
  waypoints
  maps
  DESTINATION share/${PROJECT_NAME}
)

# Lint/testing (optional)
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

