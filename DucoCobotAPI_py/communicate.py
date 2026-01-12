#!/usr/bin/env python
import os
import rospy
from std_msgs.msg import String  # 可以根据需要替换为自定义消息类型
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from sample_realsense import sample_observation
from test_move2aruco import catch_with_obj_pose

class ROSCommunicationNode:
    def __init__(self, target_ip):

        # 设置ROS环境变量
        os.environ['ROS_MASTER_URI'] = f"http://{target_ip}:11311"
        os.environ['ROS_IP'] = '10.188.210.28' # self.get_local_ip()  # 自动获取本机IP
        print(f"\n=== 环境变量 ===")
        print(f"ROS_MASTER_URI: {os.environ.get('ROS_MASTER_URI')}")
        print(f"ROS_IP: {os.environ.get('ROS_IP')}\n")

        # 初始化ROS节点
        rospy.init_node('ros_image_sender', anonymous=True)

        # 初始化CV桥
        self.bridge = CvBridge()
        
        # 设置目标IP
        self.target_ip = target_ip
        
        # 创建发布者 (发送图片)
        self.image_pub = rospy.Publisher('/image_transfer', Image, queue_size=10)

        # 创建订阅者，监听来自目标IP的回复
        # 注意: 实际使用时需要根据目标节点的发布话题进行修改
        rospy.Subscriber('/image_response', String, self.response_callback)
        
        # 处理算法就绪标志
        self.algorithm_ready = False

    def get_local_ip(self):
        """获取本机IP地址"""
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP
    
    def send_message(self, rgb_img, depth_img):
        # try:
        # 转换为ROS消息
        rgb_image = self.bridge.cv2_to_imgmsg(rgb_img, "bgr8")
        rgb_image.header.stamp = rospy.Time.now()
        rgb_image.header.frame_id = "rgb_img"
        self.image_pub.publish(rgb_image)
        rospy.loginfo(f"已发送图片: rgb_img (大小: {rgb_img.shape})")
        
        depth_image = self.bridge.cv2_to_imgmsg(depth_img, "mono8")
        depth_image.header.stamp = rospy.Time.now()
        depth_image.header.frame_id = "depth_img"
        self.image_pub.publish(depth_image)
        rospy.loginfo(f"已发送图片: rgb_img (大小: {depth_image.shape})")
        # except Exception as e:
        #     rospy.logerr(f"处理图片时出错: {str(e)}")
    
    def response_callback(self, response_msg):
        """接收来自目标节点的回复"""
        rospy.loginfo(f"收到来自 {self.target_ip} 的回复: {response_msg.data}")
        
        # 启动处理算法
        self.process_response(response_msg.data)
    
    def process_response(self, response_data):
        """处理回复的算法"""
        rospy.loginfo("启动处理算法...")

        obj2eye = response_data
        status = catch_with_obj_pose(obj2eye)
        # 这里实现你的处理逻辑
        try:
            # 示例处理 - 可以根据需要修改
            status = catch_with_obj_pose(obj2eye)
            rospy.loginfo(f"处理结果: {status}")
            
            # 标记算法已完成
            self.algorithm_ready = True
        except Exception as e:
            rospy.logerr(f"处理过程中发生错误: {str(e)}")
    
    def run(self):
        """主运行循环"""
        rgb_img, depth_img = sample_observation()
        rate = rospy.Rate(1)  # 1Hz
        while not rospy.is_shutdown():
            if self.algorithm_ready:
                break
            # 示例: 每隔一段时间发送一次消息
            # 实际使用时可以根据需要修改或移除
            self.send_message(rgb_img, depth_img)
            rate.sleep()

if __name__ == '__main__':
    try:
        # 替换为目标节点的实际IP
        target_ip = "10.138.41.252"  # 示例IP，请修改为实际目标IP
        
        node = ROSCommunicationNode(target_ip)
        node.run()
    except rospy.ROSInterruptException:
        pass