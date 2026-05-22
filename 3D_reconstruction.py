import os
import subprocess

# ==================== 配置参数 ====================
project_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output\0001"

realityCapture_url = r"C:\Program Files\Epic Games\RealityScan_2.1\RealityScan.exe"

realityCapture_params_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\params.xml"
# ==================== 三维重建 ====================
"""
步骤3：三维重建

功能说明：
    使用Realityscan软件对前景图像进行摄影测量和三维重建。
    该步骤将从多视角的2D图像中重建出完整的3D模型。

技术细节：
    - 软件：RealityScan (专业摄影测量软件)
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
    9. 保存项目：保存RealityScan项目文件

输出文件：
    - 3D模型：output/{项目名}/labels/{项目名}.ply
    - 项目文件：output/{项目名}/project/{项目名}.rcproj

性能提示：
    - 该步骤需要大量计算资源，建议使用高性能GPU
    - 处理时间取决于图像数量和分辨率，150张图像约需10-30分钟
"""
project_name = os.path.basename(project_url)
project_file = os.path.join(project_url, 'project', f"{project_name}.rcproj")
fore_dir = os.path.join(project_url, 'fore')
ply_path = os.path.join(project_url, 'labels', f"{project_name}.ply")

os.makedirs(os.path.join(project_url, 'project'), exist_ok=True)
os.makedirs(os.path.join(project_url, 'labels'), exist_ok=True)

print(f"\n开始三维重建: {project_name}")

# 步骤1：添加图像、对齐、合并组件并保存项目
r1 = subprocess.run([
    realityCapture_url,
    "-addFolder", fore_dir,
    "-align",
    "-mergeComponents",

    "-save", project_file,
    "-quit"
])
print(f"步骤1 返回码: {r1.returncode}")
print(f"项目文件存在: {os.path.exists(project_file)}")

# 步骤2：加载已对齐项目、重建模型并导出
r2 = subprocess.run([
    realityCapture_url,
    "-load", project_file,
    "-setReconstructionRegionAuto",
    "-calculateHighModel",
    "-calculateVertexColors",
    "-calculateTexture",
    "-exportModel", "Model 1", ply_path,
    "-save", project_file,
    "-quit"
])
print(f"步骤2 返回码: {r2.returncode}")
print(f"PLY文件存在: {os.path.exists(ply_path)}")
print(f"PLY路径: {ply_path}")

print("三维重建完成。")
