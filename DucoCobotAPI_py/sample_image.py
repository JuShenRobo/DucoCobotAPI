import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os

# 配置 RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = pipeline.start(config)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is:", depth_scale)

align = rs.align(rs.stream.color)

# 参数配置
save_root = '/home/adminpc/DucoCobotAPI/DucoCobotAPI_py/deliver_imgs'
record_timestamps_path = os.path.join(save_root, "record_timestamps.txt")
AFTER_SAVE_DELAY = 3  # 保存完后延迟3秒退出

try:
    # 等待一帧准备就绪
    for _ in range(30):
        frames = pipeline.wait_for_frames()

    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)
    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()

    if not aligned_depth_frame or not color_frame:
        raise RuntimeError("未能获取图像帧")

    # 获取图像数据
    depth_data = np.asanyarray(aligned_depth_frame.get_data(), dtype="float16")
    depth_image = np.asanyarray(aligned_depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())
    depth_mapped_image = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

    # 显示图像
    cv2.imshow("live", np.hstack((color_image, depth_mapped_image)))
    cv2.waitKey(1)

    # 自动保存一次
    timestamp_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    save_path = os.path.join(save_root, timestamp_str)
    os.makedirs(os.path.join(save_path, "color"))
    os.makedirs(os.path.join(save_path, "depth"))

    with open(record_timestamps_path, "a") as f:
        f.write(timestamp_str + "\n")

    cv2.imwrite(os.path.join(save_path, "color", "0.png"), color_image)
    np.save(os.path.join(save_path, "depth", "0"), depth_data)
    cv2.imwrite(os.path.join(save_path, "depth", "0.png"), depth_image)
    print(f"[INFO] 图像已保存至 {save_path}")

    cv2.imshow("save", np.hstack((color_image, depth_mapped_image)))
    cv2.waitKey(1)

    # 等待几秒然后退出
    time.sleep(AFTER_SAVE_DELAY)
    cv2.destroyAllWindows()

finally:
    pipeline.stop()
