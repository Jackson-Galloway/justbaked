#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>
#include <yaml-cpp/yaml.h>
#include <fstream>
#include <vector>
#include <string>

class DetermineFireLocation : public rclcpp::Node
{
public:
    DetermineFireLocation()
        : Node("determine_fire_location")
    {
        // Subscribe to the temperature sensor topic
        temp_sub_ = this->create_subscription<std_msgs::msg::Float32>(
            "/temperature", 10, std::bind(&DetermineFireLocation::temp_callback, this, std::placeholders::_1));

        // Timer to periodically check and update the fire location
        timer_ = this->create_wall_timer(
            std::chrono::seconds(5),
            std::bind(&DetermineFireLocation::check_fire_location, this)
        );
    }

private:
    // Callback for the temperature sensor data
    void temp_callback(const std_msgs::msg::Float32::SharedPtr msg)
    {
        // Store the temperature data for later comparison
        current_temp_ = msg->data;
    }

    // Determine which corner has the highest temperature and update round2.yaml
    void check_fire_location()
    {
        // Define the corners and their associated coordinates (e.g., hardcoded or obtained from sensors)
        // Each corner will have coordinates and a name
        std::vector<std::tuple<std::string, float, float, float>> corners = {
            {"corner1", 0.0, 0.0, 0.0},  // Example coordinates and name
            {"corner2", 5.0, 0.0, 0.0},  // Example coordinates and name
            {"corner3", 5.0, 5.0, 0.0}   // Example coordinates and name
        };

        // Find the corner with the highest temperature
        std::string fire_corner;
        float max_temp = -999.0;  // Initialize with a low value
        float fire_x = 0.0, fire_y = 0.0, fire_yaw = 0.0;

        for (const auto& corner : corners)
        {
            // For now, we're assuming the temperature from the sensor is always the same
            // for all corners, but you can modify the logic based on actual temperature readings
            if (current_temp_ > max_temp)  // Replace with actual logic if available
            {
                fire_corner = std::get<0>(corner);
                fire_x = std::get<1>(corner);
                fire_y = std::get<2>(corner);
                fire_yaw = std::get<3>(corner);  // Assuming 0.0 yaw, adjust if needed
                max_temp = current_temp_;  // Update with the latest temperature
            }
        }

        // Now update the round2.yaml file with the selected corner's coordinates
        YAML::Node config;
        config["fire_location"]["x"] = fire_x;
        config["fire_location"]["y"] = fire_y;
        config["fire_location"]["yaw"] = fire_yaw;

        // Write the updated data to round2.yaml
        std::ofstream fout("/path/to/round2.yaml");  // Update this path as necessary
        fout << config;
        fout.close();

        RCLCPP_INFO(this->get_logger(), "Fire location chosen: %s at (%.2f, %.2f, %.2f)",
                    fire_corner.c_str(), fire_x, fire_y, fire_yaw);
    }

    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr temp_sub_;
    rclcpp::TimerBase::SharedPtr timer_;
    float current_temp_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DetermineFireLocation>());
    rclcpp::shutdown();
    return 0;
}

