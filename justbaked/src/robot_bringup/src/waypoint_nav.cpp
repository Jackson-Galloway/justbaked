#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <yaml-cpp/yaml.h>
#include <fstream>

class WaypointNavNode : public rclcpp::Node {
public:
  using NavigateToPose = nav2_msgs::action::NavigateToPose;
  using GoalHandleNavigate = rclcpp_action::ClientGoalHandle<NavigateToPose>;

  WaypointNavNode() : Node("waypoint_nav_cpp_node"), current_index_(0) {
    RCLCPP_INFO(get_logger(), "WaypointNavNode started");

    nav_to_pose_client_ = rclcpp_action::create_client<NavigateToPose>(
      this, "navigate_to_pose");

    load_waypoints();

    timer_ = this->create_wall_timer(
      std::chrono::seconds(5),
      std::bind(&WaypointNavNode::go_to_next_waypoint, this));
  }

private:
  rclcpp_action::Client<NavigateToPose>::SharedPtr nav_to_pose_client_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::vector<geometry_msgs::msg::PoseStamped> waypoints_;
  size_t current_index_;

  void load_waypoints() {
    std::string path = this->get_parameter_or<std::string>(
      "waypoints_file",
      std::string("/home/ieee/justbaked/justbaked/src/robot_bringup/waypoints/round1.yaml"));

    YAML::Node config = YAML::LoadFile(path);
    for (const auto & wp : config["waypoints"]) {
      geometry_msgs::msg::PoseStamped pose;
      pose.header.frame_id = "map";
      pose.pose.position.x = wp["x"].as<double>();
      pose.pose.position.y = wp["y"].as<double>();
      double yaw = wp["yaw"].as<double>();
      tf2::Quaternion q;
      q.setRPY(0, 0, yaw);
      pose.pose.orientation = tf2::toMsg(q);
      waypoints_.push_back(pose);
    }
  }

  void go_to_next_waypoint() {
    if (current_index_ >= waypoints_.size()) {
      RCLCPP_INFO(this->get_logger(), "All waypoints visited.");
      return;
    }

    if (!nav_to_pose_client_->wait_for_action_server(std::chrono::seconds(5))) {
      RCLCPP_ERROR(this->get_logger(), "Nav2 action server not available");
      return;
    }

    auto goal_msg = NavigateToPose::Goal();
    goal_msg.pose = waypoints_[current_index_];

    rclcpp_action::Client<NavigateToPose>::SendGoalOptions options;
    options.goal_response_callback = std::bind(
      &WaypointNavNode::goal_response_cb, this, std::placeholders::_1);
    options.feedback_callback = std::bind(
      &WaypointNavNode::feedback_cb, this, std::placeholders::_1, std::placeholders::_2);
    options.result_callback = std::bind(
      &WaypointNavNode::result_cb, this, std::placeholders::_1);

    nav_to_pose_client_->async_send_goal(goal_msg, options);
  }

  void goal_response_cb(GoalHandleNavigate::SharedPtr handle) {
    if (!handle) {
      RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
    } else {
      RCLCPP_INFO(this->get_logger(), "Goal accepted");
    }
  }

  void feedback_cb(GoalHandleNavigate::SharedPtr,
                   const std::shared_ptr<const NavigateToPose::Feedback> feedback) {
    RCLCPP_INFO(this->get_logger(), "Distance remaining: %.2f m",
                feedback->distance_remaining);
  }

  void result_cb(const GoalHandleNavigate::WrappedResult & result) {
    switch (result.code) {
      case rclcpp_action::ResultCode::SUCCEEDED:
        RCLCPP_INFO(this->get_logger(), "Reached waypoint %zu", current_index_);
        break;
      case rclcpp_action::ResultCode::ABORTED:
        RCLCPP_ERROR(this->get_logger(), "Goal was aborted");
        return;
      case rclcpp_action::ResultCode::CANCELED:
        RCLCPP_ERROR(this->get_logger(), "Goal was canceled");
        return;
      default:
        RCLCPP_ERROR(this->get_logger(), "Unknown result code");
        return;
    }

    current_index_++;
    go_to_next_waypoint();
  }
};

int main(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<WaypointNavNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
