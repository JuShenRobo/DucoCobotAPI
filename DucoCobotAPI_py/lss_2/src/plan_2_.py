#!/usr/bin/env python

import rospy
from lss_2.msg import Plan, status
import os
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import re
import numpy as np
import ast


class PlannerNode:
    def __init__(self):
        self.plan_pub = rospy.Publisher('/plan', Plan, queue_size=10)
        self.status_pub = rospy.Publisher('/status', status, queue_size=10)
        self.nav_sub = rospy.Subscriber('/nav', status, self.nav_callback)
        self.grasp_sub = rospy.Subscriber('/grasp', status, self.grasp_callback)
        self.current_plan = Plan()
        self.current_plan.actions, self.current_plan.poses= self.get_tasks_from_user_new()  #第一个是子任务列表，第二个是空间位姿列表
        self.status=status()
        self.status.nav_status=[False]*len(self.current_plan.actions)
        self.current_task_index = 0
        rospy.sleep(1)  # 确保发布者和订阅者已经连接
        self.execute_current_task()  #先迭代第一个子任务

    def llm_response(self,input_instruction):
        category_names = [
                "Bottle", "Box", "Bucket", "Cart", "CoffeeMachine", "Dispenser",
                "Door", "KitchenPot", "Microwave", "Oven", "Refrigerator", "Remote",
                "Safe", "StorageFurniture", "Suitcase", "Table", "TrashCan", "WashingMachine",
                "Camera", "Chair", "Clock", "Dishwasher", "Display", "Eyeglasses",
                "Fan", "Faucet", "FoldingChair", "Globe", "Kettle", "Keyboard", 
                "Knife", "Lamp", "Laptop", "Lighter", "Mouse", "Pen", 
                "Phone", "Pliers", "Printer", "Scissors", "Stapler", "Switch",
                "Toaster", "Toilet", "USB", "Window", "Packaging", "Sponge"
        ]

        # Example 1:
        # Instruction: "pick the bottle on the table and put it to the pot in the sink"
        # ["Navigate: go to bottle", "Manipulate: pick bottle", "Navigate: go to KitchenPot", "Manipulate: put KitchenPot"]

        # Example 2:
        # Instruction: "Take something to wipe the desktop"
        # ["Navigate: go to Sponge", "Manipulate: pick Sponge", "Navigate: go to Table", "Manipulate: put Table"]

        gpt3_context = """
        You are given an instruction and scene objects for performing a task. 
        Please break the instruction down into a sequence of subtasks. The output should be a list where each element is formatted as "Navigate: go to object" or "Manipulate: action object".

        Please follow these rules:
        - Only use the four actions provided ("pick", "put", "throw", "pour").
        - For "Navigate," directly refer to the object that needs to be picked, format as "go to something".
        - For "Manipulate," if the action is "pick," specify the object being picked.
        - If using put, do not output the structure of 'put something to something', only output 'put targeted-object'
        - If using pour, do not output the structure of 'pour something to something', only output 'pour targeted-object'
        - If using throw, do not output the structure of 'throw something to something', only output 'throw targeted-object'
        - Ensure that the subtasks are ordered correctly between navigation and manipulation.
        - Output the subtasks in the following format:
        [list of navigation or manipulation steps]

        Now, scene objects are: "{category_names}", generate the subtasks for the following instruction: "{input_instruction}"
        """


        def make_prompt(found_objects,input_instruction):

            scene_description = found_objects
            formatted_prompt = gpt3_context.format(category_names=found_objects, input_instruction=input_instruction)
            return formatted_prompt
        #需要指定好什么东西在哪里，以及要做什么任务
        # input_instruction = "pick the bottle and put it to the pot"
        # input_instruction = "pick the bottle and pour the water in the pot"
        # input_instruction = "clean the desk" #还没设置好任务
        # input_instruction = "Get an electronic devices and let me sit down to rest"
        found_objects=category_names
        gpt3_prompt=make_prompt(found_objects,input_instruction)  
        # print(gpt3_prompt)

        key = "sk-s9WYCN6J3aoSqhD7cquadBpA8jvS7s061koYnKF9oOrapFvp" #"r"your key"     # 我使用的是closeai，换成自己的GPT4-api
        base = "https://api.openai-proxy.org/v1" #"https://api.openai-proxy.org" #r"your base"
        server = "none"  #r"https://u284241-a083-3edacbc8.westc.gpuhub.com:8443/"
        os.environ["OPENAI_API_KEY"] = key
        os.environ["OPENAI_API_BASE"] = base


        def get_gpt4_response():
            system_message = SystemMessage(content=gpt3_prompt)
            human_message=HumanMessage(content=input_instruction)
            messages = [
                system_message, #读入prompt
                human_message
            ]
            llm=ChatOpenAI(
                        model_name="gpt-3.5-turbo",
                        temperature=0,
                        request_timeout=120,
                    )
            response = llm(messages).content



            return response

        tasks=get_gpt4_response()
        # print("subtask_list",tasks)
        # 使用正则表达式提取列表部分
        subtask_list = [line.strip() for line in tasks.strip()[1:-1].strip().splitlines() if line.strip()]
        

        return subtask_list

    def get_tasks_from_user(self):

        query=input(f"What do you want me to do?\nEnter your query:")   #take a cup of water
        ##query输入大模型得到subtasks
        # tasks=["pick the cup from the table","take the cup to the sink to collect water","place the cup on the tray of the table"]
        tasks=["pick up the bottle", "put in the kitchenpot"]
        print("the steps are as follows:",tasks)
        ##从场景中得出每个subtask的位姿转向
        task1_pos='(0.795898, 0.628072, 0.000000, 0.000000, 0.000000, 0.942148, 0.335196)'  
        task2_pos='(4.693160, -2.443259, 0.000000, 0.000000, 0.000000, 0.573697, 0.819067)'
        task3_pos='(2.405841, -1.689561, 0.000000, 0.000000, 0.000000, 0.969136, 0.246526)'
        tasks_pos=[task1_pos,task2_pos,task3_pos]

        # tasks = []
        # num_tasks = int(input("Enter the number of tasks: "))
        # for i in range(num_tasks):
        #     task = input(f"Enter task {i + 1}: ")
        #     tasks.append(task)
        return tasks,tasks_pos
    
    def get_tasks_from_user_new(self):
        query=input(f"What do you want me to do?\nEnter your query:")   #take a cup of water
        ##query输入大模型得到subtasks
        # query="Take something to wipe the desktop, then pick the something to throw into the trash can"
##以下
        output=self.llm_response(query)

        # tasks=["pick the cup from the table","take the cup to the sink to collect water","place the cup on the tray of the table"]
        # tasks=["pick up the bottle", "put in the kitchenpot"]
        # print("the steps are as follows:",tasks)
        ##需要对每个nav subtask给定位姿，这里要求不重复到一个地方，故重复的位姿task_pos就令为false

##以下
        tasks_all=[]
        tasks_nav=[]
        tasks_grasp=[]
        for task in output:
            if "nav" in task.lower():
                result =  task.split(",")[0].strip() #task.split(":")[1].split(",")[0].strip()
                tasks_all.append(result)
                tasks_nav.append(result)
            elif "man" in task.lower():
                result = task.split(",")[0].strip()   #task.split(":")[1].split(",")[0].strip()
                tasks_all.append(result)
                tasks_grasp.append(result)
        print(tasks_all)
        # print(tasks_nav)
        # print(tasks_grasp)
        
        tasks_pos=[]
        for i in range(len(tasks_all)):
            if "nav" in tasks_all[i].lower():
                ##迭代出tasks_pos
                tasks_pos.append('1')
            elif "man" in tasks_all[i].lower():
                tasks_pos.append('0')


        # tasks_all=['"Navigate: go to Bottle"', '"Manipulate: pick Bottle"', '"Navigate: go to KitchenPot"', '"Manipulate: put Bottle to KitchenPot"']
        # tasks_all=['"Manipulate: pick Bottle"', '"Manipulate: put Bottle to KitchenPot"']
        task1_pos='(0.795898, 0.628072, 0.000000, 0.000000, 0.000000, 0.942148, 0.335196)'  
        task2_pos='(4.693160, -2.443259, 0.000000, 0.000000, 0.000000, 0.573697, 0.819067)'
        task3_pos='(2.405841, -1.689561, 0.000000, 0.000000, 0.000000, 0.969136, 0.246526)'
        tasks_pos=[task1_pos,'0',task2_pos,'0']
        # tasks_pos=[task1_pos,task2_pos,task3_pos]
        self.current_plan.poses=tasks_pos

        return tasks_all,tasks_pos
    
    def nav_callback(self, msg):
        status = msg.nav_status
        if status[self.current_task_index]:  #识别该下标的任务是否完成了
            self.current_task_index=self.current_task_index+1
            self.execute_current_task()

    # def send_grasp_task(self,nav,grasp):
    #     if nav[self.current_task_index] and not grasp[self.current_task_index]:
    #         # rospy.loginfo(f"Sending task {self.current_task_index + 1} to grasping module: [' {self.current_plan.actions[self.current_task_index]}']")
    #         self.plan_pub.publish(self.current_plan)


    def grasp_callback(self, msg):
        status = msg.nav_status
        if status[self.current_task_index]:  #识别该下标的任务是否完成了
            self.current_task_index=self.current_task_index+1
            self.execute_current_task()


    def execute_current_task(self):
        if self.current_task_index < len(self.current_plan.actions):
            if "nav" in self.current_plan.actions[self.current_task_index].lower():
                rospy.loginfo(f"Sending task {self.current_task_index + 1} to Navigate module: [' {self.current_plan.actions[self.current_task_index]}']")
            else:
                rospy.loginfo(f"Sending task {self.current_task_index + 1} to Manipulate module: [' {self.current_plan.actions[self.current_task_index]}']")
            # rospy.loginfo(f"Sending task {self.current_task_index + 1} to navigation module: [' {self.current_plan.actions[self.current_task_index]}']")
            self.current_plan.current_task_index=self.current_task_index
            self.plan_pub.publish(self.current_plan)
            # self.status_pub.publish(self.status)
        else:
            rospy.loginfo("All tasks completed")

if __name__ == '__main__':
    rospy.init_node('planner_node')
    PlannerNode()
    rospy.spin()
