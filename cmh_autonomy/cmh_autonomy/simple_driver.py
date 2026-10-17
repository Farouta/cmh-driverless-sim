"""Minimal example node: drive the car at a constant speed and log the measured speed."""

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class SimpleDriver(Node):
    """Publish a constant command on /cmd_vel and log the speed reported on /odom."""

    def __init__(self) -> None:
        super().__init__('simple_driver')
        self.declare_parameter('target_speed', 1.0)  # [m/s]
        self.declare_parameter('yaw_rate', 0.0)  # [rad/s], converted to steering by Gazebo

        self.speed = 0.0
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_timer(0.05, self.on_control_timer)  # 20 Hz
        self.create_timer(1.0, self.on_log_timer)

    def on_odom(self, msg: Odometry) -> None:
        self.speed = msg.twist.twist.linear.x

    def on_control_timer(self) -> None:
        cmd = Twist()
        cmd.linear.x = self.get_parameter('target_speed').get_parameter_value().double_value
        cmd.angular.z = self.get_parameter('yaw_rate').get_parameter_value().double_value
        self.cmd_pub.publish(cmd)

    def on_log_timer(self) -> None:
        self.get_logger().info(f'speed: {self.speed:.2f} m/s')


def main(args: list[str] | None = None) -> None:
    try:
        with rclpy.init(args=args):
            rclpy.spin(SimpleDriver())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass


if __name__ == '__main__':
    main()
