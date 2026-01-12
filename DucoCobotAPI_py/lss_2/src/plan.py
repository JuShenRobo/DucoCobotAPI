#!/usr/bin/env python

import rospy
from lss_2.msg import Plan, nav

class PlannerNode:
    def __init__(self):
        self.plan_pub = rospy.Publisher('/plan', Plan, queue_size=10)
        self.nav_sub = rospy.Subscriber('/nav', nav, self.nav_callback)
        self.current_plan = Plan()
        self.current_plan.actions, self.current_plan.poses= self.get_tasks_from_user()
        self.nav_status = [False] * len(self.current_plan.actions)
        self.current_task_index = 0
        rospy.sleep(1)  # 确保发布者和订阅者已经连接
        self.execute_current_task()  #先迭代第一个子任务

    def get_tasks_from_user(self):
        query=input(f"What do you want me to do?\nEnter your query:")   #take a cup of water
        ##query输入大模型得到subtasks
        tasks=["pick the cup from the table","take the cup to the sink to collect water","place the cup on the tray of the table"]
        print("the steps are as follows:",tasks)
        ##从场景中得出每个subtask的位姿转向
        task1_pos='(0.795898, 0.628072, 0.000000, 0.000000, 0.000000, 0.942148, 0.335196)'   #电脑桌
        task2_pos='(4.962536, -2.894589, 0.000000, 0.000000, 0.000000, 0.122370, 0.992485)' #水池
        task3_pos='(2.405841, -1.689561, 0.000000, 0.000000, 0.000000, 0.969136, 0.246526)'  #桌子
        tasks_pos=[task1_pos,task2_pos,task3_pos]

        # tasks = []
        # num_tasks = int(input("Enter the number of tasks: "))
        # for i in range(num_tasks):
        #     task = input(f"Enter task {i + 1}: ")
        #     tasks.append(task)
        return tasks,tasks_pos
    
    def nav_callback(self, msg):
        self.nav_status = msg.status
        if self.nav_status[self.current_task_index]:  #识别该下标的任务是否完成了
            rospy.loginfo(f"Task {self.current_task_index + 1} completed")
            self.current_task_index += 1
            self.current_plan.current_task_index=self.current_task_index
            self.execute_current_task()

    def execute_current_task(self):
        if self.current_task_index < len(self.current_plan.actions):
            rospy.loginfo(f"Sending task {self.current_task_index + 1} to navigation module: [' {self.current_plan.actions[self.current_task_index]}']")
            self.plan_pub.publish(self.current_plan)
        else:
            rospy.loginfo("All tasks completed")

if __name__ == '__main__':
    rospy.init_node('planner_node')
    PlannerNode()
    rospy.spin()
