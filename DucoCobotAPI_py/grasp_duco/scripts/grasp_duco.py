import rospy
import cv2
import numpy as np
import os
import pexpect
import signal
from math import radians, cos, sin
import re
import concurrent.futures
from msg import camera, pose
from SiasunRobot import SiasunRobotPythonInterface
from scipy.spatial.transform import Rotation as R

robot = SiasunRobotPythonInterface() 

img_msg = None
camera2base = []

# 创建一个节点
rospy.init_node('grasp_7010')

def run_command(command):
    child = pexpect.spawn('/bin/bash', ['-c', command], encoding='utf-8')
    child.logfile = open('/tmp/pexpect.log', 'w')  # 用于调试
    try:
        child.expect(pexpect.EOF, timeout=90)
    except pexpect.exceptions.TIMEOUT:
        print(f"Timeout: {command} did not finish in time.")
    stdout = child.before
    stderr = child.after  # 捕获 EOF 之后的输出
    return child  # 返回 child 对象用于后续终止

def run_command_with_outputs(command):
    """
    执行命令并捕获输出（适用于 Python 或其他交互式命令）
    """
    child = pexpect.spawn('/bin/bash', ['-c', command], encoding='utf-8')
    child.logfile = open('/tmp/pexpect.log', 'w')  # 用于调试
    
    try:
        # 捕获所有输出，直到进程结束
        child.expect(pexpect.EOF, timeout=90)
        output = child.before  # 获取全部输出
    except pexpect.exceptions.TIMEOUT:
        print(f"Timeout: {command} did not finish in time.")
        output = child.before  # 超时前已输出的内容
    finally:
        child.logfile.close()
    return output, child  # 返回输出字符串和子进程对象（可选）

def run_command_with_inputs(command, input_texts):
    child = pexpect.spawn('/bin/bash', ['-c', command], encoding='utf-8')
    child.logfile = open('/tmp/pexpect.log', 'w')  # Used for debugging
    try:
        for text in input_texts:
            child.sendline(text)
        child.expect(pexpect.EOF)
        stdout = child.before
        stderr = child.after  # Capture output after EOF
    except pexpect.EOF:
        stdout = child.before
        stderr = ''  # Handle EOF error
    finally:
        child.logfile.close()
        child.close(force=True)
    return stdout, stderr

# def run_command_with_inputs(command, input_prompts, input_texts, exit_input='e'):
#     child = pexpect.spawn('/bin/bash', ['-c', command], encoding='utf-8')
#     child.logfile = open('/tmp/pexpect.log', 'w')  # Used for debugging
#     try:
#         for prompt, text in zip(input_prompts, input_texts):
#             child.expect(prompt)
#             child.sendline(text)
#             if text == exit_input:
#                 print('######### realsense data collected!')
#                 child.sendintr()   # ctrl+c
#                 break
#         child.expect(pexpect.EOF)
#         stdout = child.before
#         stderr = child.after  # Capture output after EOF
#     except pexpect.EOF:
#         stdout = child.before
#         stderr = ''  # Handle EOF error
#     finally:
#         child.logfile.close()
#         child.close(force=True)
#     return stdout, stderr

def euler_to_rotation_matrix(rx, ry, rz):
    """将欧拉角 (Rx, Ry, Rz) 转换为 3x3 旋转矩阵 (ZYX 顺序)"""
    rx, ry, rz = radians(rx), radians(ry), radians(rz)
    
    # 计算旋转矩阵（ZYX 顺序）
    Rz = np.array([
        [cos(rz), -sin(rz), 0],
        [sin(rz),  cos(rz), 0],
        [0,        0,       1]
    ])
    
    Ry = np.array([
        [cos(ry),  0, sin(ry)],
        [0,        1, 0],
        [-sin(ry), 0, cos(ry)]
    ])
    
    Rx = np.array([
        [1, 0,        0],
        [0, cos(rx), -sin(rx)],
        [0, sin(rx),  cos(rx)]
    ])
    
    R = Rz @ Ry @ Rx  # 组合旋转（Z → Y → X）
    return R

def string_to_homogeneous_matrix(s):
    """将字符串 '[X,Y,Z] [Rx,Ry,Rz]' 转换为 4x4 齐次矩阵"""
    # 提取数字部分
    matches = re.findall(r"[-+]?\d*\.\d+|\d+", s)
    if len(matches) != 6:
        raise ValueError("输入格式错误！应为 '[X,Y,Z] [Rx,Ry,Rz]'")
    
    # 解析 XYZ 和 Rx,Ry,Rz
    x, y, z = map(float, matches[:3])
    rx, ry, rz = map(float, matches[3:6])
    
    # 计算旋转矩阵
    R = euler_to_rotation_matrix(rx, ry, rz)
    
    # 构建齐次矩阵
    T = np.eye(4)
    T[:3, :3] = R      # 旋转部分
    T[:3, 3] = [x, y, z]  # 平移部分
    return T

def imgpath(par_path):
    record_timestamps_path = os.path.join(par_path, "record_timestamps.txt")
    # read timestamps
    with open(record_timestamps_path, "r") as file:
        timestamps = file.read().splitlines()

    # get latest timestamp
    if timestamps:
        latest_timestamp = timestamps[-1]
    else:
        print("No timestamps found in the file.")

    OUT_PATH = os.path.join(par_path, latest_timestamp)
    IMAGE_PATH = os.path.join(OUT_PATH, "color/0.png")
    DEPTH_PATH = os.path.join(OUT_PATH, "depth/0.npy")
    return IMAGE_PATH, DEPTH_PATH

def deliver_image(IMAGE_PATH, DEPTH_PATH):
    img_msg = camera()
    img = cv2.imread(IMAGE_PATH)
    img_msg.size = list(img.shape)
    size = img_msg.size[0]*img_msg.size[1]*img_msg.size[2]
    img_msg.color = img.reshape(size).tolist()
    depth_npy = np.load(DEPTH_PATH)
    img_msg.depth = depth_npy.flatten().tolist()
    return img_msg

def rotation_matrix_to_euler(R_matrix):
    """
    将旋转矩阵转换为欧拉角
    """
    rotation = R.from_matrix(R_matrix)
    euler_angles = rotation.as_euler('xyz', degrees=True)  # 返回的是 [roll, pitch, yaw]
    return euler_angles

def move2obj(pose):
    translation = pose[:3, 3]*1000 # 转换为mm
    rotation = pose[:3, :3]
    euler_angles = rotation_matrix_to_euler(rotation) # 得到degree制的欧拉角
    # 将translation和euler合并为一个列表
    transformed_pose = [float(translation[0]), float(translation[1]), float(translation[2])] + \
                    [90.04, 2.91, 88.81]
                    #    [float(euler_angles[0]), float(euler_angles[1]), float(euler_angles[2])]
    catch_ready_pose = [float(translation[0]), float(translation[1]) - 100, float(translation[2])] + \
                    [90.04, 2.91, 88.81]
                    #    [float(euler_angles[0]), float(euler_angles[1]), float(euler_angles[2])]

    print("transformed_pose:", transformed_pose)

    ret = robot.moveJ_pose(catch_ready_pose)
    ret = robot.moveJ_pose(transformed_pose)

    print("moveJ ret:", ret)

def callback2(camera):
    rospy.loginfo('Sub 2: camera ready!')
    rospy.sleep(1)

def callback4(pose):
    global T_tcp2base, img_msg
    rospy.loginfo('Sub 4: pose received!')
    obj2eye = np.array(pose.pose).reshape(4, 4)
    # eye2tcp
    eye2tcp_path = os.path.join("/home/adminpc/robotics/eye_hand_calib/data", "eye2tcp_matrix.txt")
    eye2tcp = np.loadtxt(eye2tcp_path)
    eye2tcp[:3, 3] = eye2tcp[:3, 3] / 1000 # convert to meters
    grasp_pose = T_tcp2base @ eye2tcp @ obj2eye
    # np.savetxt('/home/user/catkin_ws/grasp_pose.txt', grasp_pose)
    rospy.loginfo('pose saved!')
    move2obj(grasp_pose)
    img_msg = None
    

if __name__ == '__main__':
    while not rospy.is_shutdown():
        pub3 = rospy.Publisher('/image', camera, queue_size=10)
        sub2 = rospy.Subscriber('/camera', camera, callback2)

        rospy.wait_for_message("/camera", camera, timeout=None)

        commands = [
            "cd /home/adminpc/DucoCobotAPI/DucoCobotAPI_py && python SiasunRobot.py",
            "cd /home/user/DucoCobotAPI/DucoCobotAPI_py && python sample_realsense.py"
        ]

        input_texts = ['s', 'q']

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            # for command in commands[:-1]:  # 最后一个命令是交互式的
            #     print("##### DO...")
            #     # futures.append(run_command(command))
            #     futures.append(executor.submit(run_command, command))
            #     print("##### DONE...")
            tcp2base, child = run_command(commands[0])
            futures.append(executor.submit(run_command_with_inputs, commands[-1], input_texts))

            # 等待所有命令完成
            stdout, stderr = futures[-1].result()
            print("Standard Output:", stdout)
            print("Standard Error:", stderr)
            for future in futures[:-1]:  # 不包括第四个命令本身
                print('### KILLING...: ', future)
                try:
                    result = future.result(timeout=5)  # 设置超时为5秒
                except concurrent.futures.TimeoutError:
                    print("Task did not complete in time, attempting to terminate...")
                    # 强制终止进程
                    for proc in executor._processes.values():
                        if proc.is_alive():
                            proc.terminate()
                            print(f"Process {proc.pid} terminated.")
                print('### KILLED...')
        print("##### All commands executed.")

        rospy.loginfo('image delivering...')
        # img_msg = deliver_image('/home/user/PTY/2024_07_30_19_43_05/0100_color.png')

        T_tcp2base = string_to_homogeneous_matrix(tcp2base)
        data_path = '/home/adminpc/DucoCobotAPI/DucoCobotAPI_py/deliver_imgs'
        img_msg = deliver_image(imgpath(data_path))
        pub3.publish(img_msg)
        rospy.loginfo('Pub 3: image delivered!')

        sub4 = rospy.Subscriber('/pose', pose, callback4)
        rospy.wait_for_message("/pose", pose, timeout=None)
        camera2base = []
        print("-------任务执行结束-------")
        rospy.sleep(2)