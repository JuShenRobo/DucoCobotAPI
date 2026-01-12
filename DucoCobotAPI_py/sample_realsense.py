"""

Realsense Capture.

"""

"""

    - Author: Tianyu Wang
    - Creation Time: 2023/10/18

"""

import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os

def sample_observation():
    pipeline = rs.pipeline()

    # Create a config and pipeline
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    profile = pipeline.start(config)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    print("Depth Scale is: " , depth_scale)

    align_to = rs.stream.color
    align = rs.align(align_to)

    # saved image and realtime image
    cv2.namedWindow("live", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("save", cv2.WINDOW_AUTOSIZE)
    saved_color_image = None # saved temporary image
    saved_depth_mapped_image = None
    saved_count = 0

# Main Loop
    try:
        while True:
            frames = pipeline.wait_for_frames()

            aligned_frames = align.process(frames)

            aligned_depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not aligned_depth_frame or not color_frame:
                continue

            depth_data = np.asanyarray(aligned_depth_frame.get_data(), dtype="float16")
            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            depth_mapped_image = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
            cv2.imshow("live", np.hstack((color_image, depth_mapped_image)))
            key = cv2.waitKey(30)

            # s - save image
            if key & 0xFF == ord('s'):

                # get current time
                current_time = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
                save_path = os.path.join('/home/adminpc/DucoCobotAPI/DucoCobotAPI_py/deliver_imgs', current_time)

                record_timestamps_path = os.path.join('/home/adminpc/DucoCobotAPI/DucoCobotAPI_py/deliver_imgs', "record_timestamps.txt")
                
                # record timestamps
                with open(record_timestamps_path, "a") as file:
                    file.write(current_time + "\n")

                os.mkdir(save_path)
                os.mkdir(os.path.join(save_path, "color"))
                os.mkdir(os.path.join(save_path, "depth"))
                saved_color_image = color_image
                saved_depth_mapped_image = depth_mapped_image

                # image to png
                print('save_path', save_path)
                cv2.imwrite(os.path.join((save_path), "color", "{}.png".format(saved_count)), saved_color_image)
                # depth to npy
                np.save(os.path.join((save_path), "depth", "{}".format(saved_count)), depth_data)
                # depth.png saves
                cv2.imwrite(os.path.join((save_path), "depth","{}.png".format(saved_count)),depth_image)
                saved_count+=1
                cv2.imshow("save", np.hstack((saved_color_image, saved_depth_mapped_image)))

                cv2.destroyAllWindows()
                break
        return saved_color_image, saved_depth_mapped_image
    finally:
        pipeline.stop()
