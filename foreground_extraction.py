from tqdm import tqdm  # 用于显示循环进度条
import glob  # 用于查找符合特定规则的文件路径名
import os  # 提供与操作系统交互的功能，如文件和目录操作
import subprocess  # 用于执行外部命令和子进程管理

# 设置ONNX Runtime使用GPU加速
# 创建包含GPU设置的环境变量字典
import copy
env_vars = copy.copy(os.environ)
env_vars['CUDA_VISIBLE_DEVICES'] = '0'  # 使用第一个GPU
# 添加open3d_env环境的Scripts目录到PATH，以便找到rembg.exe
env_vars['PATH'] = r'C:\Users\26457\anaconda3\envs\open3d_env\Scripts;' + env_vars.get('PATH', '')
env_vars['ORT_EXECUTION_PROVIDERS'] = 'CUDAExecutionProvider'
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
# 输出结果目录（存放中间处理结果和项目文件）
# 只处理output/0001/original目录下的文件
target_original = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output\0001\original"
target_fore = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output\0001\fore"

rembg_exe = r'C:\Users\26457\anaconda3\envs\open3d_env\Scripts\rembg.exe'
os.makedirs(target_fore, exist_ok=True)

image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
images = [f for f in os.listdir(target_original) if os.path.splitext(f)[1].lower() in image_exts]

print(f"找到 {len(images)} 张图像，开始处理...")

failed = []
for fname in tqdm(images, desc="前景提取", unit="张"):
    src = os.path.join(target_original, fname)
    name, _ = os.path.splitext(fname)
    dst = os.path.join(target_fore, name + ".png")

    result = subprocess.run([
        rembg_exe, "i", "-m", "birefnet-general", "-x",
        r'{"model_path": "C:\Users\26457\BiRefNet-general-epoch_244.onnx", "providers": ["CUDAExecutionProvider", "CPUExecutionProvider"]}',
        src, dst
    ], capture_output=True, text=True, env=env_vars)

    if result.returncode != 0:
        failed.append((fname, result.stderr.strip()))

if failed:
    print(f"\n以下 {len(failed)} 张图像处理失败:")
    for fname, err in failed:
        print(f"  {fname}: {err}")
else:
    print("\n所有图像处理完成。")
