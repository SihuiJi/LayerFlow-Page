import os
import cv2
import imageio

def resample_video(input_path, output_path, target_fps=8):
    # 打开输入视频文件
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_path}")
        return
    
    # 获取视频的原始帧率、宽度和高度
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Original FPS: {original_fps}, {target_fps}")
    # 计算帧间隔，用于帧率转换
    frame_interval = int(original_fps / target_fps)
    print(f"Frame interval: {frame_interval}")
    # 创建输出视频文件
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height))

    # 读取并重采样视频帧
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_idx = 0

    for i in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        
        # 仅在间隔到达时写入帧，确保帧率降低
        if i % int(frame_interval) == 0:
            out.write(frame)
        
        frame_idx += 1
    
    # 释放资源
    cap.release()
    out.release()

def concatenate_videos_in_subfolder(subfolder_path, output_filename, target_fps=8):
    video_files = [f for f in os.listdir(subfolder_path) if f.endswith('.mp4') and not f.endswith('_concatenated.mp4') and not 'resampled_' in f]
    
    if not video_files:
        print(f"No MP4 files found in {subfolder_path}")
        return

    # 分离以rgba开头的文件和其他文件
    rgba_files = [f for f in video_files if len(f) > 20]
    if len(rgba_files) == 0:
        return
    # 将-2.mp4的视频放在-3.mp4的视频前面
    files_2 = [f for f in video_files if f.endswith('-2.mp4') or f.endswith('-2-new.mp4')]
    files_3 = [f for f in video_files if f.endswith('-3.mp4') or f.endswith('-3-new.mp4')]

    # 先处理以rgba开头的文件，然后是以-2结尾的视频，再是以-3结尾的视频，最后是其他文件
    ordered_files = files_2 + rgba_files + files_3

    # 对每个视频文件进行重采样
    resampled_videos = []
    for video_file in ordered_files:
        input_video_path = os.path.join(subfolder_path, video_file)
        output_video_path = os.path.join(subfolder_path, f"resampled_{video_file}")
        
        # 重采样并保存新视频
        resample_video(input_video_path, output_video_path, target_fps)
        resampled_videos.append(output_video_path)

    # 初始化 VideoCapture 对象和视频属性
    caps = []
    for video_file in resampled_videos:
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_file}")
            return
        caps.append(cap)

    # 获取第一个视频的宽度和高度
    width = sum(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) for cap in caps)
    height = int(caps[0].get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 使用统一的帧率
    fps = target_fps

    # 使用 imageio 创建视频写入对象
    writer = imageio.get_writer(output_filename, fps=fps)

    while True:
        # 从每个视频文件读取一帧并拼接
        frames = []
        for idx, cap in enumerate(caps):
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
        if subfolder == "bp":
            continue
        # if not subfolder == "1-1":
        #     continue
        subfolder_path = os.path.join(root_folder, subfolder)
        if os.path.isdir(subfolder_path):
            output_filename = os.path.join(subfolder_path, f"{subfolder}_concatenated.mp4")
            print(output_filename)
            concatenate_videos_in_subfolder(subfolder_path, output_filename)

if __name__ == "__main__":
    root_folder = "bg2fg-rgba"  # 替换为您的根文件夹路径
    process_subfolders(root_folder)