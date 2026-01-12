#!/usr/bin/env python

import rospy
from point_navigation import NavTest
from lss_2.msg import Plan, status
from geometry_msgs.msg import Pose, Point, Quaternion, Twist,PoseStamped
class NavigationNode:
    def __init__(self):
        self.plan_sub = rospy.Subscriber('/plan', Plan, self.plan_callback)
        # self.status_pub=rospy.Subscriber('/status', status, self.callback_1)
        self.nav_pub = rospy.Publisher('/nav', status, queue_size=10)
        self.tasks = None
        self.current_plan = None
        self.current_task_index = 0
        self.status=status()
        

    def callback_1(self,msg):
        self.nav_status=msg.nav_status
        # print("here",self.nav_status)


    def plan_callback(self, msg):
        self.tasks = msg.actions
        self.current_plan = msg.poses
        self.current_task_index=msg.current_task_index
        if not self.status.nav_status:
            self.status.nav_status=[False]*len(msg.actions)
    

        if "nav" in self.tasks[self.current_task_index].lower() and self.status.nav_status[self.current_task_index]!=True:
            rospy.loginfo('My task delivered!')
            self.execute_task()
        # if not self.status_msg.nav_status:
        #     self.status_msg.nav_status = [False] * len(self.current_plan)
        #     self.status_msg.grasp_status = [False] * len(self.current_plan)


    def execute_task(self):
        # if self.current_task_index < len(self.current_plan) and self.status_msg.nav_status[self.current_task_index]:
        #     return
            
        if self.current_task_index < len(self.current_plan):
            task = self.tasks[self.current_task_index]
            pose=self.current_plan[self.current_task_index]
            # print("all",self.current_plan)
            # print("pose",pose)

            rospy.loginfo(f"Executing nav task: {task}")
            # 去掉括号并将字符串拆分为数值
            task1_values = pose.strip('()').split(', ')

            # 将字符串转换为浮点数
            task1_values = [float(value) for value in task1_values]

            # 拆分task1
            position = tuple(task1_values[:3])
            orientation = tuple(task1_values[3:])
            # print("1",position)
            # print("2",orientation)
            location  = Pose(Point(position[0],position[1],position[2]),Quaternion(orientation[0],orientation[1],orientation[2],orientation[3]))
            # 在这里执行任务的代码，例如调用一个函数执行任务
            rospy.sleep(2)  # 模拟任务执行时间
            self.task_completed(location)
        else:
            rospy.loginfo("No more tasks to execute")

    def task_completed(self,location=None):
        NavTest(message=location)
        rospy.loginfo(f"Task {self.current_task_index + 1} completed nav period")
        self.status.nav_status = [True if i == self.current_task_index else False for i in range(len(self.current_plan))]
        # print(status_msg.nav_status)
        self.nav_pub.publish(self.status)


if __name__ == '__main__':
    rospy.init_node('navigation_node')
    NavigationNode()
    rospy.spin()