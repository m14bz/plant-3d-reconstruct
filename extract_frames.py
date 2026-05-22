import cv2
import os
import sys
from pathlib import Path
import os
import re

def create_next_image_folder(base_dir, prefix="image_"):
    """
    在 base_dir 下创建 image_x 文件夹（x 自动递增）
    """
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    pattern = re.compile(rf"{re.escape(prefix)}(\d+)$")

    max_index = 0
    for name in os.listdir(base_dir):
        full_path = os.path.join(base_dir, name)
        if os.path.isdir(full_path):
            match = pattern.match(name)
            if match:
                index = int(match.group(1))
                max_index = max(max_index, index)

    new_folder_name = f"{prefix}{max_index + 1}"
    new_folder_path = os.path.join(base_dir, new_folder_name)
    os.makedirs(new_folder_path)

    return new_folder_path


def extract_frames(video_path, output_dir, total_frames):
    """
    从视频中均匀抽取指定数量的帧

    参数:
        video_path: 输入视频路径
        output_dir: 输出图像目录
        total_frames: 要抽取的总帧数
    """
    # 检查视频文件是否存在
    if not os.path.exists(video_path):
        print(f"错误: 视频文件不存在: {video_path}")
        return False

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 打开视频
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"错误: 无法打开视频文件: {video_path}")
        return False

    # 获取视频信息
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"视频信息:")
    print(f"  总帧数: {total_video_frames}")
    print(f"  帧率: {fps:.2f} FPS")
    print(f"  时长: {total_video_frames/fps:.2f} 秒")
    print(f"  将抽取: {total_frames} 帧\n")

    if total_frames > total_video_frames:
        print(f"警告: 要抽取的帧数({total_frames})大于视频总帧数({total_video_frames})")
        total_frames = total_video_frames

    # 计算抽帧间隔
    frame_interval = total_video_frames / total_frames

    extracted_count = 0

    for i in range(total_frames):
        # 计算要读取的帧位置
        frame_idx = int(i * frame_interval)

        # 设置视频位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

        # 读取帧
        ret, frame = cap.read()

        if ret:
            # 保存图像
            output_path = os.path.join(output_dir, f"frame_{i+1:04d}.jpg")
            cv2.imwrite(output_path, frame)
            extracted_count += 1
            print(f"已保存: {output_path} (原视频第 {frame_idx} 帧)")
        else:
            print(f"警告: 无法读取第 {frame_idx} 帧")

    cap.release()

    print(f"\n完成! 成功抽取 {extracted_count} 帧到目录: {output_dir}")
    return True


if __name__ == "__main__":
    # ===== 配置参数 (在这里修改) =====
    base_dir = "./image_total"
    new_folder = create_next_image_folder(base_dir)
    print("新建文件夹：", new_folder)

    VIDEO_PATH = "vedio/IMG_9503.MOV"          # 输入视频路径
    OUTPUT_DIR =new_folder            # 输出图像目录
    TOTAL_FRAMES = 200                       # 要抽取的总帧数
    # ================================

    # 如果通过命令行传参则使用命令行参数
    if len(sys.argv) == 4:
        VIDEO_PATH = sys.argv[1]
        OUTPUT_DIR = sys.argv[2]
        TOTAL_FRAMES = int(sys.argv[3])
    elif len(sys.argv) > 1:
        print("用法:")
        print(f"  方式1 - 修改脚本中的配置参数后运行:")
        print(f"    python {sys.argv[0]}")
        print(f"  方式2 - 使用命令行参数:")
        print(f"    python {sys.argv[0]} <视频路径> <输出目录> <抽取帧数>")
        print(f"\n示例:")
        print(f"    python {sys.argv[0]} video.mp4 frames 50")
        sys.exit(1)

    print("=" * 60)
    print("视频抽帧工具")
    print("=" * 60)
    print(f"输入视频: {VIDEO_PATH}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"抽取帧数: {TOTAL_FRAMES}")
    print("=" * 60 + "\n")

    extract_frames(VIDEO_PATH, OUTPUT_DIR, TOTAL_FRAMES)
