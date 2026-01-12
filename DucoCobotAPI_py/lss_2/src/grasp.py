#!/usr/bin/env python

import rospy
from lss_2.msg import Plan,status


class GraspingNode:
    def __init__(self):
        rospy.Subscriber('/plan', Plan, self.grasp_callback)
        # rospy.Subscriber('/status', status, self.callback_1)
        self.grasp_pub = rospy.Publisher('/grasp', status, queue_size=10)
        self.tasks = None
        self.current_plan = None
        self.current_task_index = 0
        self.status=status()

    def grasp_callback(self, msg):
        self.tasks = msg.actions
        self.current_task_index = msg.current_task_index
        


        if not self.status.nav_status:
            self.status.nav_status=[False]*len(msg.actions)

        if "man" in self.tasks[self.current_task_index].lower():
            print("2")
            self.execute_task()

    def callback_1(self,msg):
        self.status=msg.nav_status


    def execute_task(self):
        if self.current_task_index < len(self.tasks) and not self.status.nav_status[self.current_task_index]:
        # if self.current_task_index < len(self.tasks):
            # if self.status.nav_status[self.current_task_index]:
                task = self.tasks[self.current_task_index]
                rospy.loginfo(f"Executing grasp task: {task}")

                # 在这里执行任务的代码，例如调用一个函数执行任务
                rospy.sleep(2)  # 模拟任务执行时间
                self.task_completed(task)
        else:
            rospy.loginfo("No more tasks to execute")

    def task_completed(self,task=None):
        ##这里根据task写你的grasp执行代码，要求执行成功才能继续执行下去
        rospy.loginfo(f"Task {self.current_task_index + 1} completed grasp period")
        self.status.nav_status = [True if i == self.current_task_index else False for i in range(len(self.tasks))]  #赋值当前子任务index下的状态值为true
        # print(self.status_msg.status)
        self.grasp_pub.publish(self.status)  #发布状态值，给规划模块接收


if __name__ == '__main__':
    rospy.init_node('grasping_node')
    GraspingNode()
    rospy.spin()
