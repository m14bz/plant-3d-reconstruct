#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速测试脚本
用于验证GPU配置是否正确，以及测试前景提取性能
"""
import os
import sys
import time
from pathlib import Path
import glob

print("=" * 70)
print("GPU 加速配置检测与性能测试")
print("=" * 70)

# 1. 检查ONNX Runtime
print("\n【1/5】检查 ONNX Runtime:")
try:
    import onnxruntime as ort
    print(f"   ✓ ONNX Runtime 版本: {ort.__version__}")

    providers = ort.get_available_providers()
    print(f"   ✓ 可用的执行提供者: {providers}")

    has_cuda = 'CUDAExecutionProvider' in providers
    has_directml = 'DmlExecutionProvider' in providers

    if has_cuda:
        print("   ✓ NVIDIA CUDA 加速: 可用")
        selected_providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        gpu_type = "NVIDIA CUDA"
    elif has_directml:
        print("   ✓ DirectML 加速: 可用 (AMD/Intel显卡)")
        selected_providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
        gpu_type = "DirectML"
    else:
        print("   ✗ GPU 加速: 不可用")
        selected_providers = ['CPUExecutionProvider']
        gpu_type = "CPU"

except ImportError as e:
    print(f"   ✗ 错误: {e}")
    print("\n   安装方法:")
    print("   pip install onnxruntime-gpu")
    sys.exit(1)

# 2. 检查rembg
print("\n【2/5】检查 rembg:")
try:
    from rembg import remove
    from PIL import Image
    print("   ✓ rembg 已安装")
    print("   ✓ Pillow 已安装")
except ImportError as e:
    print(f"   ✗ 导入失败: {e}")
    print("\n   安装方法:")
    print("   pip install rembg[gpu] pillow")
    sys.exit(1)

# 3. 检查环境变量
print("\n【3/5】检查环境变量:")
cuda_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '未设置')
ort_providers = os.environ.get('ORT_EXECUTION_PROVIDERS', '未设置')
print(f"   CUDA_VISIBLE_DEVICES: {cuda_devices}")
print(f"   ORT_EXECUTION_PROVIDERS: {ort_providers}")

# 4. 检查自定义模型
print("\n【4/5】检查自定义模型:")
custom_model_path = r"C:\Users\26457\BiRefNet-general-epoch_244.onnx"
if os.path.exists(custom_model_path):
    print(f"   ✓ 找到自定义模型: {custom_model_path}")
    file_size = os.path.getsize(custom_model_path) / (1024 * 1024)  # MB
    print(f"   ✓ 模型大小: {file_size:.1f} MB")
    use_custom_model = True
else:
    print(f"   ✗ 未找到自定义模型")
    print(f"   将使用默认的 birefnet-general 模型")
    use_custom_model = False

# 5. 性能测试
print("\n【5/5】性能测试:")

# 查找测试图像
test_image_dirs = [
    r"C:\Users\26457\Desktop\demo-3d-reconstruction\output",
    r"E:\BaiduNetdiskDownload\自动三维重建脚本\images"
]

test_image = None
for test_dir in test_image_dirs:
    if os.path.exists(test_dir):
        # 查找第一张图像
        for pattern in ['*.JPG', '*.jpg', '*.JPEG', '*.jpeg', '*.PNG', '*.png']:
            images = glob.glob(os.path.join(test_dir, '**', pattern), recursive=True)
            if images:
                test_image = images[0]
                break
        if test_image:
            break

if test_image and os.path.exists(test_image):
    print(f"   ✓ 找到测试图像: {Path(test_image).name}")
    print(f"   执行提供者: {gpu_type}")

    try:
        # 加载图像
        input_image = Image.open(test_image)
        width, height = input_image.size
        print(f"   图像尺寸: {width} x {height} 像素")

        # 测试处理速度
        print(f"\n   开始处理测试（使用 {gpu_type}）...")
        start_time = time.time()

        if use_custom_model:
            output_image = remove(
                input_image,
                session_kwargs={
                    'providers': selected_providers,
                    'model_path': custom_model_path
                }
            )
        else:
            output_image = remove(
                input_image,
                session_kwargs={'providers': selected_providers},
                model_name='birefnet-general'
            )

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"   ✓ 处理成功！")
        print(f"   ✓ 处理时间: {processing_time:.2f} 秒")

        # 性能评估
        print(f"\n   性能评估:")
        if has_cuda or has_directml:
            if processing_time < 2:
                rating = "⭐⭐⭐⭐⭐ 优秀"
                status = "GPU加速正常工作"
            elif processing_time < 5:
                rating = "⭐⭐⭐⭐ 良好"
                status = "GPU加速生效"
            elif processing_time < 10:
                rating = "⭐⭐⭐ 一般"
                status = "可能未完全利用GPU"
            else:
                rating = "⭐⭐ 较慢"
                status = "可能在使用CPU，请检查GPU配置"
        else:
            if processing_time < 10:
                rating = "⭐⭐ CPU模式"
                status = "建议启用GPU加速"
            else:
                rating = "⭐ CPU模式较慢"
                status = "强烈建议启用GPU加速"

        print(f"   性能评级: {rating}")
        print(f"   状态: {status}")

        # 估算批量处理时间
        estimate_150 = processing_time * 150
        print(f"\n   估算处理150张图像:")
        print(f"   - 总耗时: {estimate_150 / 60:.1f} 分钟 ({estimate_150:.0f} 秒)")

        # 保存测试结果
        output_path = "test_output.png"
        output_image.save(output_path)
        print(f"\n   ✓ 测试结果已保存: {output_path}")

    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        print(f"\n   详细错误信息:")
        traceback.print_exc()

else:
    print("   ✗ 未找到测试图像")
    print("   提示: 请在以下目录放置测试图像:")
    for dir_path in test_image_dirs:
        print(f"   - {dir_path}")

# 总结
print("\n" + "=" * 70)
print("检测完成 - 配置总结")
print("=" * 70)

if has_cuda:
    print("✓ GPU加速: NVIDIA CUDA 已启用")
elif has_directml:
    print("✓ GPU加速: DirectML 已启用 (AMD/Intel)")
else:
    print("✗ GPU加速: 未启用")
    print("\n如何启用GPU加速:")
    print("-" * 70)
    print("NVIDIA 显卡用户:")
    print("  1. 确保安装了NVIDIA驱动和CUDA")
    print("  2. pip uninstall onnxruntime onnxruntime-gpu -y")
    print("  3. pip install onnxruntime-gpu")
    print("\nAMD/Intel 显卡用户:")
    print("  1. pip uninstall onnxruntime onnxruntime-gpu -y")
    print("  2. pip install onnxruntime-directml")
    print("-" * 70)

print("\n运行 foreground_extraction.py 开始批量处理图像")
print("=" * 70)