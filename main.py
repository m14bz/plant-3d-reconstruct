"""
3D重建自动化流程脚本

功能概述：
    这是一个自动化的3D重建流程脚本，用于批量处理图像并生成3D模型。
    整个流程包括：项目创建、前景提取、三维重建和三维预处理四个主要步骤。

主要步骤：
    1. 创建项目：根据图像数量自动创建项目文件夹结构
    2. 前景提取：使用rembg工具移除图像背景，提取前景对象
    3. 三维重建：使用RealityCapture软件进行3D重建
    4. 三维预处理：使用Open3D对生成的3D模型进行后处理

依赖项：
    - Python库：glob, tqdm, pathlib, shutil, os, subprocess, open3d, rembg
    - 外部软件：RealityCapture
    - 模型文件：birefnet-general.onnx
"""

import glob  # 用于查找符合特定规则的文件路径名
from tqdm import tqdm  # 用于显示循环进度条
from pathlib import Path  # 提供面向对象的文件系统路径操作
from shutil import copyfile  # 用于文件的复制操作
import os  # 提供与操作系统交互的功能，如文件和目录操作
import subprocess  # 用于执行外部命令和子进程管理
import open3d as o3d  # 用于3D数据处理和可视化

# ==================== 配置参数 ====================
# 原始图像存放目录
base_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\image_total\image_2"

# 输出结果目录（存放中间处理结果和项目文件）
output_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output"

# 最终数据集目录（存放处理完成的点云数据）
dataset_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\dataset"

# RealityCapture软件的可执行文件路径
realityCapture_url = r"C:\Program Files\Capturing Reality\RealityCapture\RealityCapture.exe"

# 3D重建的参数配置XML文件路径
realityCapture_params_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\params.xml"

# 每个项目包含的图像数量（每150张图像创建一个新项目）
img_num = 150

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

# ==================== 前景提取 ====================
"""
步骤2：前景提取

功能说明：
    使用rembg工具移除图像背景，提取前景对象。
    这一步将生成透明背景的图像，便于后续3D重建时更准确地识别物体轮廓。

技术细节：
    - 工具：rembg (Remove Background)
    - 模型：birefnet-general (高质量通用前景提取模型)
    - 模型文件：birefnet-general.onnx
    - 处理方式：批量处理模式 (rembg p)

输入输出：
    - 输入：output/{项目名}/original/ 目录下的原始图像
    - 输出：output/{项目名}/fore/ 目录下的透明背景图像

性能提示：
    - 该步骤非常耗时，150张图像可能需要30-60分钟
    - 支持GPU加速，建议使用支持CUDA的GPU
"""
print("\n开始前景提取...")

# 遍历所有项目的original目录
for image_url in tqdm(glob.glob(os.path.join(output_url, '*', 'original'))):
    print(f"正在处理图像: {image_url}")

    # 调用rembg命令行工具进行批量前景提取
    # 参数说明：
    #   rembg p: 批量处理模式
    #   -m birefnet-general: 使用birefnet-general模型（高精度通用模型）
    #   -x: 传递额外的JSON格式参数
    #   model_path: 指定模型文件的本地路径
    #   第一个路径: 输入目录 (original)
    #   第二个路径: 输出目录 (fore)
    result = subprocess.run([
        "python", "-m", "rembg", "p", "-m", "birefnet-general", "-x",
        r'{"model_path": ""C:\Users\26457\BiRefNet-general-epoch_244.onnx""}',
        image_url,
        image_url.replace('original', 'fore')  # 将original替换为fore作为输出目录
    ], capture_output=True, text=True)

# ==================== 三维重建 ====================
"""
步骤3：三维重建

功能说明：
    使用RealityCapture软件对前景图像进行摄影测量和三维重建。
    该步骤将从多视角的2D图像中重建出完整的3D模型。

技术细节：
    - 软件：RealityCapture (专业摄影测量软件)
    - 输入：前景提取后的透明背景图像
    - 输出：高精度3D模型（PLY格式）和项目文件（.rcproj）

重建流程：
    1. 添加图像：导入fore目录下的所有前景图像
    2. 对齐：计算相机位置和姿态
    3. 合并组件：合并所有对齐的图像组
    4. 设置重建区域：自动确定3D重建的范围
    5. 计算高精度模型：生成高质量的三维网格
    6. 计算顶点颜色：为模型添加颜色信息
    7. 计算纹理：生成真实感纹理贴图
    8. 导出模型：保存为PLY格式
    9. 保存项目：保存RealityCapture项目文件

输出文件：
    - 3D模型：output/{项目名}/labels/{项目名}.ply
    - 项目文件：output/{项目名}/project/{项目名}.rcproj

性能提示：
    - 该步骤需要大量计算资源，建议使用高性能GPU
    - 处理时间取决于图像数量和分辨率，150张图像约需10-30分钟
"""
print("\n开始三维重建...")

print(os.path.join(project_url, 'fore'))
# 遍历所有项目目录
for project_url in tqdm(glob.glob(os.path.join(output_url, '*'))):
    # 获取项目名称
    project_name = Path(project_url).name
    project_file = os.path.join(project_url, 'project', f"{project_name}.rcproj")

    # 步骤1：对齐图像并保存项目
    subprocess.run([
        realityCapture_url,
        "-addFolder", os.path.join(project_url, 'fore'),
        "-align",
        "-mergeComponents",
        "-save", project_file,
        "-quit"
    ])

    # 步骤2：加载项目、选择组件并计算模型
    subprocess.run([realityCapture_url,
                    "-addFolder", os.path.join(project_url, 'fore'),
                    "-align",
                    "-mergeComponents",
                    "-setReconstructionRegionAuto",
                    "-calculateHighModel",
                    "-calculateVertexColors",
                    "-calculateTexture",
                    "-exportModel", "Model 1", os.path.join(project_url, 'labels', f"{project_name}.ply"),
                    realityCapture_params_url,
                    "-save", os.path.join(project_url,
                    'project', f"{project_name}.rcproj"),
                    "-quit"
                    ])

# ==================== 三维预处理 ====================
"""
步骤4：三维预处理

功能说明：
    使用Open3D对生成的3D网格模型进行后处理，生成清洁的点云数据。
    这一步可以去除噪声和离群点，提高数据质量，便于后续分析和应用。

技术细节：
    - 工具：Open3D (开源3D数据处理库)
    - 输入：OBJ格式的三维网格模型
    - 输出：清洁的PLY格式点云文件

处理流程：
    1. 读取网格模型：从labels目录加载OBJ文件
    2. 均匀采样：从网格表面均匀采样10000个点
    3. 离群点过滤：使用半径滤波去除噪声点
    4. 保存点云：将清洁的点云保存到dataset目录

参数说明：
    - number_of_points: 采样点数（10000）
      建议范围：5000-50000，根据模型复杂度调整

    - nb_points: 最少邻近点数（3）
      含义：在搜索半径内至少需要3个邻近点才保留
      增加该值可以更严格地过滤离群点

    - radius: 搜索半径（0.05）
      单位：与模型尺度相关
      需根据实际模型大小调整

输出文件：
    - 清洁点云：dataset/{项目名}.ply
"""
print("\n开始三维预处理...")

# 遍历所有项目的labels目录中的OBJ文件
for mesh_url in tqdm(glob.glob(os.path.join(output_url, '*', 'labels', '*.obj'))):
    # 读取三维网格模型
    mesh = o3d.io.read_triangle_mesh(mesh_url)

    # 步骤1：从网格表面进行均匀采样
    # 这会在网格表面均匀分布地采样10000个点
    pcd = mesh.sample_points_uniformly(number_of_points=10000)

    # 步骤2：使用半径滤波去除离群点
    # nb_points=3: 在半径范围内至少需要3个邻近点
    # radius=0.05: 搜索半径为0.05个单位
    # 返回过滤后的点云和保留点的索引
    pcd, ind = pcd.remove_radius_outlier(nb_points=3, radius=0.05)

    # 步骤3：准备输出路径
    mesh_path_obj = Path(mesh_url)
    # 将文件扩展名从.obj改为.ply
    ply_filename = mesh_path_obj.with_suffix('.ply').name
    # 构建最终输出路径
    dataset_ply_path = Path(dataset_url) / ply_filename

    # 确保dataset目录存在
    Path(dataset_url).mkdir(parents=True, exist_ok=True)

    # 步骤4：保存处理后的点云
    o3d.io.write_point_cloud(str(dataset_ply_path), pcd)

print("\n所有处理完成!")
