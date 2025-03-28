import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile
from std_msgs.msg import Int32
from gpiozero import Servo
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Quaternion
from tf2_ros import TransformException
from tf2_geometry_msgs import do_transform_pose
import yaml
import math
import time
from enum import Enum

class State(Enum):
    TO_LATCH = 1
    TURN_180 = 2
    BACK_UP = 3
    TO_HOME = 4
    FACE_FIRE = 5
    LAUNCH_CATAPULT = 6
    DONE = 7

class WaypointNavNode(Node):
    def __init__(self):
        super().__init__('waypoint_nav_node')
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.state = State.TO_LATCH
        self.backup_complete = False

        # Initialize poses
        self.waypoints = []
        self.latch_pose = PoseStamped()
        self.home_pose = PoseStamped()
        self.fire_pose = PoseStamped()
        self.load_waypoints()
        self.set_latch_position()
        self.home_pose.header.frame_id = 'map'
        self.home_pose.pose.position.x = 0.0
        self.home_pose.pose.position.y = 0.0
        self.home_pose.pose.position.z = 0.0
        self.home_pose.pose.orientation = self.create_quaternion(0.0)

        # Timer to execute state machine
        self.timer = self.create_timer(5.0, self.execute_state_machine)

    def load_waypoints(self):
        waypoints_file = self.get_parameter_or(
            'waypoints_file', 
            '/home/ieee/justbaked/justbaked/src/robot_bringup/waypoints/round1.yaml'
        ).get_parameter_value().string_value
        with open(waypoints_file, 'r') as file:
            config = yaml.safe_load(file)
            for wp in config['waypoints']:
                pose = PoseStamped()
                pose.header.frame_id = 'map'
                pose.pose.position.x = float(wp['x'])
                pose.pose.position.y = float(wp['y'])
                pose.pose.orientation = self.create_quaternion(float(wp['yaw']))
                self.waypoints.append(pose)
        # Assume fire waypoint is the last one (adjust as needed)
        self.fire_pose = self.waypoints[-1]
        self.get_logger().info(f"Loaded {len(self.waypoints)} waypoints")

    def set_latch_position(self):
        self.latch_pose.header.frame_id = 'map'
        self.latch_pose.pose.position.x = 0.470  # 0.470 m ahead
        self.latch_pose.pose.position.y = -0.102  # -0.102 m left
        self.latch_pose.pose.position.z = 0.0
        self.latch_pose.pose.orientation = self.create_quaternion(0.0)

    def create_quaternion(self, yaw):
        q = Quaternion()
        q.w = math.cos(yaw / 2.0)
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        return q

    def execute_state_machine(self):
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Nav2 action server not available")
            return

        if self.state == State.TO_LATCH:
            self.get_logger().info("Navigating to just in front of latch...")
            self.send_goal(self.latch_pose, self.to_latch_callback)

        elif self.state == State.TURN_180:
            self.get_logger().info("Turning 180 degrees...")
            self.latch_pose.pose.orientation = self.turn_180(self.latch_pose.pose.orientation)
            self.send_goal(self.latch_pose, self.turn_180_callback)

        elif self.state == State.BACK_UP:
            self.get_logger().info("Backing up several inches...")
            self.backup_robot()

        elif self.state == State.TO_HOME:
            self.get_logger().info("Navigating back to origin...")
            self.send_goal(self.home_pose, self.to_home_callback)

        elif self.state == State.FACE_FIRE:
            self.get_logger().info("Facing the fire waypoint...")
            self.home_pose.pose.orientation = self.face_position(self.fire_pose.pose.position)
            self.send_goal(self.home_pose, self.face_fire_callback)

        elif self.state == State.LAUNCH_CATAPULT:
            self.get_logger().info("Launching catapult...")
            self.launch_catapult()
            self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info("Task complete.")
            self.timer.cancel()

    def send_goal(self, pose, result_callback):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose
        goal_handle_future = self.nav_to_pose_client.send_goal_async(
            goal_msg,
            feedback_callback=None
        )
        goal_handle_future.add_done_callback(
            lambda future: self.goal_response_callback(future, result_callback)
        )

    def goal_response_callback(self, future, result_callback):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            return
        self.get_logger().info("Goal accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(result_callback)

    def to_latch_callback(self, future):
        result = future.result().result
        if result and result.result == NavigateToPose.Result().SUCCESS:
            self.state = State.TURN_180

    def turn_180_callback(self, future):
        result = future.result().result
        if result and result.result == NavigateToPose.Result().SUCCESS:
            self.state = State.BACK_UP

    def turn_180(self, current):
        yaw = 2 * math.acos(current.w)  # Extract current yaw
        new_yaw = yaw + math.pi  # Add 180 degrees (π radians)
        return self.create_quaternion(new_yaw)

    def backup_robot(self):
        backup_pose = self.latch_pose
        backup_pose.pose.position.x -= 0.1524  # Back up 6 inches
        self.send_goal(backup_pose, self.backup_callback)

    def backup_callback(self, future):
        result = future.result().result
        if result and result.result == NavigateToPose.Result().SUCCESS:
            time.sleep(2)  # Wait 2 seconds
            self.backup_complete = True
            self.state = State.TO_HOME

    def to_home_callback(self, future):
        result = future.result().result
        if result and result.result == NavigateToPose.Result().SUCCESS:
            self.state = State.FACE_FIRE

    def face_fire_callback(self, future):
        result = future.result().result
        if result and result.result == NavigateToPose.Result().SUCCESS:
            self.state = State.LAUNCH_CATAPULT

    def face_position(self, target):
        dx = target.x - self.home_pose.pose.position.x
        dy = target.y - self.home_pose.pose.position.y
        yaw = math.atan2(dy, dx)
        return self.create_quaternion(yaw)

    def launch_catapult(self):
        # Replace with your servo motor control code
        self.get_logger().info("Servo motor activating catapult...")
        # Set up the servo (GPIO 5 aka Pin 29)
        self.servo = Servo(5)
        
        # Create a subscription to listen to angle values
        self.subscription = self.create_subscription(
                Int32,
                'servo_angle', # Topic name
                self.listener_callback,
                10
        )
        self.subscription # prevent unused variable warning

        angle = msg.data # Get angle from the message
        self.get_logger().info(f"Moving servo to: {angle} degrees")

        # Map the angle to the servo's range of motion (-1 to 1) (Can be adjusted based on servo)
        mapped_value = (angle - 90) / 90 # Map angle (90 degrees as neutral)

        # Move the servo to the mapped position
        self.servo.value = mapped_value
        time.sleep(1)


def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
