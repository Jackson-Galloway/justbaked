#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <std_msgs/msg/int32.hpp>
#include <yaml-cpp/yaml.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <math.h>
#include <string>
#include <vector>
#include <chrono>

using namespace std::chrono_literals;

class CatapultNode : public rclcpp::Node {
public:
  enum class State {
    TO_LATCH = 1,
    TURN_180 = 2,
    BACK_UP = 3,
    TO_HOME = 4,
    FACE_FIRE = 5,
    LAUNCH_CATAPULT = 6,
    DONE = 7
  };

  CatapultNode() : Node("catapult_node") {
    nav_to_pose_client_ = rclcpp_action::create_client<nav2_msgs::action::NavigateToPose>(
      this, "navigate_to_pose");

    // Initialize state and other parameters
    state_ = State::TO_LATCH;
    backup_complete_ = false;

    // Initialize poses
    latch_pose_ = geometry_msgs::msg::PoseStamped();
    home_pose_ = geometry_msgs::msg::PoseStamped();
    fire_pose_ = geometry_msgs::msg::PoseStamped();
    load_waypoints();
    set_latch_position();
    home_pose_.header.frame_id = "map";
    home_pose_.pose.position.x = 0.0;
    home_pose_.pose.position.y = 0.0;
    home_pose_.pose.position.z = 0.0;
    home_pose_.pose.orientation = create_quaternion(0.0);

    // Publisher for the servo
    servo_pub_ = this->create_publisher<std_msgs::msg::Int32>("servo_angle", 10);

    // Timer for the state machine
    timer_ = this->create_wall_timer(5s, std::bind(&CatapultNode::execute_state_machine, this));
  }

private:
  rclcpp_action::Client<nav2_msgs::action::NavigateToPose>::SharedPtr nav_to_pose_client_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr servo_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::vector<geometry_msgs::msg::PoseStamped> waypoints_;
  geometry_msgs::msg::PoseStamped latch_pose_;
  geometry_msgs::msg::PoseStamped home_pose_;
  geometry_msgs::msg::PoseStamped fire_pose_;
  State state_;
  bool backup_complete_;

  void load_waypoints() {
    std::string waypoints_file = this->declare_parameter<std::string>(
      "waypoints_file", "/home/ieee/justbaked/justbaked/src/robot_bringup/waypoints/round3.yaml");

    YAML::Node config = YAML::LoadFile(waypoints_file);
    for (const auto &wp : config["waypoints"]) {
      geometry_msgs::msg::PoseStamped pose;
      pose.header.frame_id = "map";
      pose.pose.position.x = wp["x"].as<double>();
      pose.pose.position.y = wp["y"].as<double>();
      double yaw = wp["yaw"].as<double>();
      pose.pose.orientation = create_quaternion(yaw);
      waypoints_.push_back(pose);
    }

    // Assuming fire waypoint is the last one (adjust as needed)
    fire_pose_ = waypoints_.back();
    RCLCPP_INFO(this->get_logger(), "Loaded %zu waypoints", waypoints_.size());
  }

  void set_latch_position() {
    latch_pose_.header.frame_id = "map";
    latch_pose_.pose.position.x = 1.524 - 0.349;  // 5 ft - 13.5" ahead
    latch_pose_.pose.position.y = 0.457 - 0.349;  // 1.5 ft - 11.5" to the side
    latch_pose_.pose.position.z = 0.0;
    latch_pose_.pose.orientation = create_quaternion(M_PI);  // 180 degrees yaw
  }

  geometry_msgs::msg::Quaternion create_quaternion(double yaw) {
    geometry_msgs::msg::Quaternion q;
    q.w = std::cos(yaw / 2.0);
    q.x = 0.0;
    q.y = 0.0;
    q.z = std::sin(yaw / 2.0);
    return q;
  }

  void execute_state_machine() {
    if (!nav_to_pose_client_->wait_for_action_server(5s)) {
      RCLCPP_ERROR(this->get_logger(), "Nav2 action server not available");
      return;
    }

    switch (state_) {
      case State::TO_LATCH:
        RCLCPP_INFO(this->get_logger(), "Navigating to just in front of latch...");
        send_goal(latch_pose_, std::bind(&CatapultNode::to_latch_callback, this, std::placeholders::_1));
        break;

      case State::TURN_180:
        RCLCPP_INFO(this->get_logger(), "Turning 180 degrees...");
        latch_pose_.pose.orientation = turn_180(latch_pose_.pose.orientation);
        send_goal(latch_pose_, std::bind(&CatapultNode::turn_180_callback, this, std::placeholders::_1));
        break;

      case State::BACK_UP:
        RCLCPP_INFO(this->get_logger(), "Backing up...");
        backup_robot();
        break;

      case State::TO_HOME:
        RCLCPP_INFO(this->get_logger(), "Navigating back to home...");
        send_goal(home_pose_, std::bind(&CatapultNode::to_home_callback, this, std::placeholders::_1));
        break;

      case State::FACE_FIRE:
        RCLCPP_INFO(this->get_logger(), "Facing the fire waypoint...");
        home_pose_.pose.orientation = face_position(fire_pose_.pose.position);
        send_goal(home_pose_, std::bind(&CatapultNode::face_fire_callback, this, std::placeholders::_1));
        break;

      case State::LAUNCH_CATAPULT:
        RCLCPP_INFO(this->get_logger(), "Launching catapult...");
        launch_catapult();
        state_ = State::DONE;
        break;

      case State::DONE:
        RCLCPP_INFO(this->get_logger(), "Task complete.");
        timer_->cancel();
        break;
    }
  }

  void send_goal(geometry_msgs::msg::PoseStamped pose, std::function<void(rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr)> result_callback) {
    auto goal_msg = nav2_msgs::action::NavigateToPose::Goal();
    goal_msg.pose = pose;

    auto goal_handle_future = nav_to_pose_client_->async_send_goal(goal_msg);
    goal_handle_future.add_done_callback(
      [this, result_callback](std::future<rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr> future) {
        auto goal_handle = future.get();
        if (goal_handle) {
          result_callback(goal_handle);
        } else {
          RCLCPP_ERROR(this->get_logger(), "Goal rejected");
        }
      }
    );
  }

  void to_latch_callback(rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr goal_handle) {
    state_ = State::TURN_180;
  }

  void turn_180_callback(rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr goal_handle) {
    state_ = State::BACK_UP;
  }

  void backup_robot() {
    latch_pose_.pose.position.x -= 0.1524;  // Back up 6 inches
    send_goal(latch_pose_, std::bind(&CatapultNode::backup_callback, this, std::placeholders::_1));
  }

  void backup_callback(rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr goal_handle) {
    backup_complete_ = true;
    state_ = State::TO_HOME;
  }

  void to_home_callback(rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr goal_handle) {
    state_ = State::FACE_FIRE;
  }

  void face_fire_callback(rclcpp_action::ClientGoalHandle<nav2_msgs::action::NavigateToPose>::SharedPtr goal_handle) {
    state_ = State::LAUNCH_CATAPULT;
  }

  geometry_msgs::msg::Quaternion turn_180(geometry_msgs::msg::Quaternion current) {
    double yaw = 2 * std::acos(current.w);  // Extract current yaw
    double new_yaw = yaw + M_PI;  // Add 180 degrees (π radians)
    return create_quaternion(new_yaw);
  }

  geometry_msgs::msg::Quaternion face_position(const geometry_msgs::msg::Point &target) {
    double dx = target.x - home_pose_.pose.position.x;
    double dy = target.y - home_pose_.pose.position.y;
    double yaw = std::atan2(dy, dx);
    return create_quaternion(yaw);
  }

  void launch_catapult() {
    // Send 36 degrees to trigger the catapult launch
    std_msgs::msg::Int32 msg;
    msg.data = 36;  // Set the angle to 36 degrees for the catapult launch
    servo_pub_->publish(msg);
  }
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CatapultNode>());
  rclcpp::shutdown();
  return 0;
}

