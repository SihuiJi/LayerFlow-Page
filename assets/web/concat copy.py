import os
import cv2
import imageio

def concatenate_videos_in_subfolder(subfolder_path, output_filename):
    video_files = [f for f in os.listdir(subfolder_path) if f.endswith('.mp4') and not f.endswith('_concatenated.mp4')]
    
    if not video_files:
        print(f"No MP4 files found in {subfolder_path}")
        return

    # 分离以rgba开头的文件和其他文件
    rgba_files = [f for f in video_files if f.startswith('rgba')]
    # 提取以-2结尾和以-3结尾的文件
    files_2 = [f for f in video_files if f.endswith('-2.mp4')]
    files_3 = [f for f in video_files if f.endswith('-3.mp4')]

    # 先处理以rgba开头的文件，然后是其他文件
    ordered_files = rgba_files + files_2 + files_3

    # 初始化 VideoCapture 对象和视频属性
    caps = []
    for video_file in ordered_files:
        cap = cv2.VideoCapture(os.path.join(subfolder_path, video_file))
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_file}")
            return
        caps.append(cap)

    # 获取视频的宽度和高度
    width = sum(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) for cap in caps)
    height = int(caps[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = caps[0].get(cv2.CAP_PROP_FPS)

    # 使用 imageio 创建视频写入对象
    writer = imageio.get_writer(output_filename, fps=fps)

    while True:
        # 从每个视频文件读取一帧并拼接
        frames = []
        for cap in caps:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)

        if len(frames) != len(caps):
            break  # 不再有完整的帧

        # 拼接帧
        combined_frame = cv2.hconcat(frames)  # 水平拼接

        # 写入拼接后的帧
        writer.append_data(cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB))

    writer.close()  # 关闭 writer

    # 释放所有视频对象
    for cap in caps:
        cap.release()
    
    print(f"Concatenated video saved as {output_filename}")
    # 保存以 segment-3.mp4 结尾的视频的第一帧
    segment_3_file = [f for f in video_files if f.endswith('-3.mp4')]
    if segment_3_file:
        segment_3_path = os.path.join(subfolder_path, segment_3_file[0])
        cap_segment_3 = cv2.VideoCapture(segment_3_path)
        if cap_segment_3.isOpened():
            ret, frame = cap_segment_3.read()  # 获取第一帧
            if ret:
                # 保存第一帧为图片
                first_frame_path = os.path.join(subfolder_path, 'first_frame_segment_3.png')
                cv2.imwrite(first_frame_path, frame)
                print(f"Saved first frame of '{segment_3_file[0]}' as {first_frame_path}")
            cap_segment_3.release()  # 释放视频对象

def process_subfolders(root_folder):
    for subfolder in os.listdir(root_folder):
        subfolder_path = os.path.join(root_folder, subfolder)
        if os.path.isdir(subfolder_path):
            output_filename = os.path.join(subfolder_path, f"{subfolder}_concatenated.mp4")
            print(output_filename)
            concatenate_videos_in_subfolder(subfolder_path, output_filename)

if __name__ == "__main__":
    root_folder = "fg2bg"  # 替换为您的根文件夹路径
    process_subfolders(root_folder)
