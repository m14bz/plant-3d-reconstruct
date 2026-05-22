import os
import open3d as o3d

# ==================== 配置参数 ====================
project_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output\0001"

dataset_url = r"C:\Users\26457\Desktop\demo-3d-reconstruction\dataset"
# ==================== 三维预处理 ====================
"""
步骤4：三维预处理

功能说明：
    使用Open3D对生成的3D网格模型进行后处理，生成清洁的点云数据。
    这一步可以去除噪声和离群点，提高数据质量，便于后续分析和应用。

技术细节：
    - 工具：Open3D (开源3D数据处理库)
    - 输入：PLY格式的三维网格模型
    - 输出：清洁的PLY格式点云文件

处理流程：
    1. 读取网格模型：从labels目录加载PLY文件
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
project_name = os.path.basename(project_url)
mesh_url = os.path.join(project_url, 'labels', f"{project_name}.ply")

print(f"\n开始三维预处理: {project_name}")
print(f"输入模型: {mesh_url}")
print(f"模型文件存在: {os.path.exists(mesh_url)}")

mesh = o3d.io.read_triangle_mesh(mesh_url)
print(f"顶点数: {len(mesh.vertices)}, 三角面数: {len(mesh.triangles)}")

pcd = mesh.sample_points_uniformly(number_of_points=10000)

pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
print(f"过滤后点数: {len(pcd.points)}")

os.makedirs(dataset_url, exist_ok=True)
output_path = os.path.join(dataset_url, f"{project_name}.ply")
o3d.io.write_point_cloud(output_path, pcd)

print(f"点云已保存: {output_path}")
