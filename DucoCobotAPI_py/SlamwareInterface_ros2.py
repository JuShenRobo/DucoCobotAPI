from geometry_msgs.msg import Pose, Point, Quaternion, Twist, PoseStamped
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from nav_msgs.msg import Odometry
import math
from slamware_ros_sdk.msg import RecoverLocalizationRequest

class SlamwareInterface(Node):
    def __init__(self):
        super().__init__('slamware_interface')
        self.current_pose = None

        self.locations = {
            'pick_table': Pose(position=Point(x=-1.906150, y=-2.728091, z=0.000000),orientation=Quaternion(x=0.000000, y=0.000000, z=0.682338, w=0.731037)),
            'place_table': Pose(position=Point(x=0.540906, y=-2.950806, z=0.000000),orientation=Quaternion(x=0.000000, y=0.000000, z=0.682780, w=0.730624))
        }
        print('saved positions:', self.locations.keys())
        
        # 创建QoS配置
        qos_profile = QoSProfile(depth=10)
        qos_profile.reliability = ReliabilityPolicy.RELIABLE
        qos_profile.durability = DurabilityPolicy.TRANSIENT_LOCAL
        
        # 创建订阅者和发布者
        self.odom_subscription = self.create_subscription(
            Odometry,
            "/slamware_ros_sdk_server_node/odom",
            self.odom_callback,
            10
        )
        
        self.pub = self.create_publisher(
            PoseStamped,
            '/move_base_simple/goal',
            qos_profile
        )
        self.ontheway_flag = False

    def odom_callback(self, data):
        self.current_pose = data
    
    def get_current_pose(self):
        return self.current_pose
    
    def calculate_distance(self,pose1, pose2):
        """计算两个位姿之间的欧几里得距离。"""
        return math.sqrt((pose1.position.x - pose2.position.x) ** 2 +
                     (pose1.position.y - pose2.position.y) ** 2 +
                     (pose1.position.z - pose2.position.z) ** 2)

    def calculate_angle_difference(self,pose1, pose2):
        """计算两个位姿之间的朝向差异（简化计算，仅以Z轴旋转为例）。"""
        # 这里的实现非常简化，实际应用中可能需要复杂的四元数或欧拉角计算
        orientation1 = pose1.orientation.z
        orientation2 = pose2.orientation.z
        return abs(orientation1 - orientation2)
    
    def nav_to_pose(self, pose):
        goal = PoseStamped()
        goal.pose = pose
        goal.header.frame_id = 'slamware_map'
        goal.header.stamp = self.get_clock().now().to_msg()
        
        while self.pub.get_subscription_count() == 0:
            self.get_logger().info("Waiting for robot base connection")
            rclpy.spin_once(self, timeout_sec=1.0)
        self.pub.publish(goal)

        self.ontheway_flag = True
        while self.get_current_pose() is None: # debug
            self.get_logger().info("Waiting for odometry data...")
            rclpy.spin_once(self, timeout_sec=0.5)
        pre_pose = self.get_current_pose().pose.pose
        while self.ontheway_flag:
            rclpy.spin_once(self, timeout_sec=0.1)
            cur_pose = self.get_current_pose().pose.pose
            position_difference_goal = self.calculate_distance(cur_pose, goal.pose)
            position_difference = self.calculate_distance(cur_pose, pre_pose)
            if position_difference < 0.01 and position_difference_goal <0.05:
                self.ontheway_flag = False
            pre_pose = cur_pose
        
        # 使用定时器替代sleep
        import time
        time.sleep(3)
    
    def nav_to_obj(self, destination):
        self.nav_to_pose(self.locations[destination])

    # def set_map(self, floor):
    #     if floor == 1:
    #         self.

    def rec_loc(self, x, y, w, h):
        pub = self.create_publisher(
            RecoverLocalizationRequest, 
            '/slamware_ros_sdk_server_node/recover_localization', 
            1
        )
        req = RecoverLocalizationRequest()
        req.area.x = x
        req.area.y = y
        req.area.w = w
        req.area.h = h
        
        while pub.get_subscription_count() == 0:
            self.get_logger().info("Waiting")
            rclpy.spin_once(self, timeout_sec=2.0)
        print("connected")
        pub.publish(req)
        print("published rec loc")
        
        import time
        time.sleep(10)
