
import glob  # 用于查找符合特定规则的文件路径名
from tqdm import tqdm  # 用于显示循环进度条
from pathlib import Path  # 提供面向对象的文件系统路径操作
from shutil import copyfile  # 用于文件的复制操作
import os  # 提供与操作系统交互的功能，如文件和目录操作
import subprocess  # 用于执行外部命令和子进程管理
import open3d as o3d  # 用于3D数据处理和可视化

# ==================== 配置参数 ====================
# 原始图像存放目录
base_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\image_total\image_3"

# 输出结果目录（存放中间处理结果和项目文件）
output_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output"

# 最终数据集目录（存放处理完成的点云数据）
dataset_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\dataset"

# RealityCapture软件的可执行文件路径
realityCapture_url = r"C:\Program Files\Capturing Reality\RealityCapture\RealityCapture.exe"

# 3D重建的参数配置XML文件路径
realityCapture_params_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\params.xml"

# 每个项目包含的图像数量（每150张图像创建一个新项目）
img_num = 200

# ==================== 创建项目 ====================
"""
步骤1：创建项目文件夹结构

功能说明：
    根据图像数量自动创建项目文件夹结构，并将原始图像分配到对应项目中。
    每150张图像创建一个新的项目文件夹。

目录结构：
    output/
    └── {项目名}/
        ├── labels/      # 存放3D模型输出文件
        ├── project/     # 存放RealityCapture项目文件
        ├── original/    # 存放原始图像副本
        └── fore/        # 存放前景提取后的图像

文件命名规则：
    图像文件名格式：*_项目名_*.JPG
    从文件名中提取项目标识符作为项目文件夹名称
"""
print("开始创建项目...")

# 记录当前正在处理的项目路径
current_url = ''
# 用于计数，判断何时创建新项目
temp_num = 0

# 遍历images目录下的所有JPG文件
for image_url in tqdm(glob.glob(os.path.join(base_url, '*.JPG'))):
    # 从文件名中提取项目名称（假设格式为：*_项目名_*.JPG）
    image_name = Path(image_url).stem.split('_')[1]

    # 每处理img_num张图像时创建一个新项目
    if temp_num % img_num == 0:
        project_url = os.path.join(output_url, image_name)
        print(project_url)
        # 检查项目文件夹是否已存在
        if os.path.exists(project_url):
            print(f"文件夹 {project_url} 已存在")
            current_url = project_url
        else:
            # 创建项目主目录
            os.mkdir(project_url)
            # 创建子目录：labels - 存放3D模型文件
            os.mkdir(os.path.join(project_url, 'labels'))
            # 创建子目录：project - 存放RealityCapture项目文件
            os.mkdir(os.path.join(project_url, 'project'))
            # 创建子目录：original - 存放原始图像
            os.mkdir(os.path.join(project_url, 'original'))
            # 创建子目录：fore - 存放前景提取后的图像
            os.mkdir(os.path.join(project_url, 'fore'))
            current_url = project_url

    # 将图像复制到当前项目的original目录
    if os.path.exists(os.path.join(current_url, 'original')):
        destination_file = os.path.join(current_url, 'original', Path(image_url).name)
        copyfile(image_url, destination_file)

    # 计数器加1
    temp_num += 1