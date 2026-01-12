#!/usr/bin/env python
from tkinter import N
import rospy
# from slamware_ros_sdk.msg import GoHomeRequest
from geometry_msgs.msg import Pose, Point, Quaternion, Twist,PoseStamped
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
# from slamware_ros_sdk.msg import GoHomeRequest
import math

from nav_msgs.msg import Odometry





class NavTest():  
    def __init__(self,message):    
        self.locations = dict()  
        # self.locations['1'] = Pose(Point(0.086323, -0.219047, 0.000000),  Quaternion(0.000000, 0.000000, -0.027541, 0.999621))  
        # self.locations['1'] = Pose(Point(4.389915, -2.967606, 0.000000),  Quaternion(0.000000, 0.000000, -0.001002, 0.999999))  


        self.pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=10, latch=True)
        
        
        self.goal = PoseStamped()  
        # i = message
        # location = str(i)    
        self.goal.pose = message  #位姿和转向
        self.goal.header.frame_id = 'slamware_map'

        while self.pub.get_num_connections() == 0:
            rospy.loginfo("Waiting")
            rospy.sleep(2)
        self.pub.publish(self.goal)  #发布点信息
        self.flag = True
        self.data0 = None
        self.subscriber = rospy.Subscriber("/slamware_ros_sdk_server_node/odom", Odometry, self.odom_callback)  #接收信息反馈
        while self.flag :
            continue
        
        self.subscriber.unregister()
        
        
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

    def odom_callback(self,data):
        # 打印接收到的位姿信息
        # orientation_difference = self.calculate_angle_difference(data.pose.pose, self.goal.pose)
        # if position_difference < 0.4:
        #     print("已到达目的地。")
        #     self.subscriber.unregister()
        # else:
        #     print("未到达目的地。")
        if self.data0 == None:
            self.data0 = data
        else:
            print(self.goal.pose)
            print(data.pose.pose)
            position_difference_goal = self.calculate_distance(data.pose.pose, self.goal.pose)
            position_difference = self.calculate_distance(self.data0.pose.pose, data.pose.pose)
            if position_difference < 0.01 and position_difference_goal <0.05:    
                print("已到达目的地。")
                self.flag = False   
            else:
                print("未到达目的地。")
            
            self.data0 = data
        
        
        # rospy.loginfo("Position: (%f, %f, %f)", data.pose.pose.position.x, data.pose.pose.position.y, data.pose.pose.position.z)
        # rospy.loginfo("Orientation: (%f, %f, %f, %f)", data.pose.pose.orientation.x, data.pose.pose.orientation.y, data.pose.pose.orientation.z, data.pose.pose.orientation.w)




if __name__ == '__main__':

    NavTest(1)
    rospy.sleep(20)