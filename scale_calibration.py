import os
import numpy as np
import open3d as o3d
import cv2
import cv2.aruco as aruco

# ==================== 配置参数 ====================
# 输入PLY点云路径（三维预处理后的输出）
ply_path = r"C:\Users\26457\Desktop\demo-3d-reconstruction\output\0001\labels\0001.ply"

# ArUco标记的实际边长（单位：米）
# 拍摄时放置在地面上的标记实物尺寸
ARUCO_MARKER_SIZE_M = 0.05

# ArUco字典类型（需与实际打印的标记一致）
ARUCO_DICT_NAME = "DICT_4X4_50"

# 俯视图投影分辨率（越大检测越准，但越慢）
TOPVIEW_IMG_PX = 2000

# ==================== 尺度校准 ====================
"""
步骤5：尺度校准（基于）

功能说明：
    从PLY点云中自动计算真实物理尺度，消除三维重建的任意尺度问题。
    无需相机内参，纯粹基于点云操作。

技术细节：
    - 方法：将点云投影为俯视图（Top-View），在图像中检测ArUco标记
    - 输入：带顶点颜色的PLY点云、已知边长的ArUco标记
    - 输出：缩放因子（scale_factor），单位：米/PLY单位

原理：
    1. 将点云按X-Y坐标投影为带颜色的俯视图像
    2. 在图像中检测ArUco标记的四个角点
    3. 将像素距离换算回PLY坐标单位，得到标记在PLY中的边长
    4. 缩放因子 = 实际边长(m) / PLY中的边长(PLY单位)

注意事项：
    - 点云必须包含顶点颜色（RealityCapture需开启-calculateVertexColors）
    - ArUco标记需朝上（从Z轴正方向可见）
    - 若检测失败，可尝试增大 TOPVIEW_IMG_PX 到 4000
"""

print("=" * 60)
print("尺度校准（ArUco俯视图检测）")
print("=" * 60)
print(f"输入点云: {ply_path}")
print(f"标记边长: {ARUCO_MARKER_SIZE_M} m")
print(f"ArUco字典: {ARUCO_DICT_NAME}")

# 读取点云
pcd = o3d.io.read_point_cloud(ply_path)
pts  = np.asarray(pcd.points)
cols = (np.asarray(pcd.colors) * 255).astype(np.uint8)

print(f"点云点数: {len(pts)}")

if len(pts) == 0:
    raise RuntimeError("点云为空，请检查PLY文件路径")
if len(cols) == 0 or cols.max() == 0:
    raise RuntimeError("点云缺少颜色信息，请确认RealityCapture开启了-calculateVertexColors")

# 构建俯视图（X-Y平面投影）
x0, y0 = pts[:, 0].min(), pts[:, 1].min()
span = max(pts[:, 0].max() - x0, pts[:, 1].max() - y0)
if span == 0:
    raise RuntimeError("点云退化（所有点重合）")

ppu = TOPVIEW_IMG_PX / span  # pixels per PLY-unit

img = np.full((TOPVIEW_IMG_PX, TOPVIEW_IMG_PX, 3), 255, dtype=np.uint8)
xi = np.clip(((pts[:, 0] - x0) * ppu).astype(int), 0, TOPVIEW_IMG_PX - 1)
yi = np.clip(((pts[:, 1] - y0) * ppu).astype(int), 0, TOPVIEW_IMG_PX - 1)
img[yi, xi] = cols[:, :3]  # RGB

print("俯视图投影完成，开始检测ArUco标记...")

# 保存俯视图（无论是否检测成功，供人工检查）
debug_topview = ply_path.replace(".ply", "_topview_debug.png")
cv2.imwrite(debug_topview, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
print(f"俯视图已保存（请打开确认ArUco是否可见）: {debug_topview}")

# 颜色统计
print(f"颜色统计: min={cols.min()} max={cols.max()} mean={cols.mean():.1f}")

adict    = aruco.getPredefinedDictionary(getattr(aruco, ARUCO_DICT_NAME))
params   = aruco.DetectorParameters()
# 放宽检测参数，提高对低分辨率点云投影的鲁棒性
params.adaptiveThreshWinSizeMin  = 3
params.adaptiveThreshWinSizeMax  = 53
params.adaptiveThreshWinSizeStep = 2
params.minMarkerPerimeterRate    = 0.01
params.maxMarkerPerimeterRate    = 4.0
params.polygonalApproxAccuracyRate = 0.05
detector = aruco.ArucoDetector(adict, params)

# 尝试三个投影轴（X-Y / X-Z / Y-Z），找到能检测到ArUco的那个
def try_detect(axis0, axis1, label):
    """将点云投影到 axis0-axis1 平面，尝试检测ArUco"""
    a0_min, a1_min = pts[:, axis0].min(), pts[:, axis1].min()
    span_ = max(pts[:, axis0].max() - a0_min, pts[:, axis1].max() - a1_min)
    if span_ == 0:
        return None, None, None
    ppu_ = TOPVIEW_IMG_PX / span_
    im = np.full((TOPVIEW_IMG_PX, TOPVIEW_IMG_PX, 3), 255, dtype=np.uint8)
    xi_ = np.clip(((pts[:, axis0] - a0_min) * ppu_).astype(int), 0, TOPVIEW_IMG_PX - 1)
    yi_ = np.clip(((pts[:, axis1] - a1_min) * ppu_).astype(int), 0, TOPVIEW_IMG_PX - 1)
    im[yi_, xi_] = cols[:, :3]
    gray_ = cv2.cvtColor(cv2.GaussianBlur(im, (5, 5), 0), cv2.COLOR_RGB2GRAY)
    # 保存各轴投影图
    cv2.imwrite(ply_path.replace(".ply", f"_topview_{label}.png"),
                cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
    c_, i_, _ = detector.detectMarkers(gray_)
    return c_, i_, ppu_

corners, ids, ppu = None, None, None
for (ax0, ax1, label) in [(0, 1, "XY"), (0, 2, "XZ"), (1, 2, "YZ")]:
    c, i, p = try_detect(ax0, ax1, label)
    if i is not None and len(i) > 0:
        print(f"  在 {label} 投影中检测到标记！")
        corners, ids, ppu = c, i, p
        break
    else:
        print(f"  {label} 投影: 未检测到")

if ids is None or len(ids) == 0:
    raise RuntimeError(
        "三个投影面（XY / XZ / YZ）均未检测到ArUco标记。\n"
        "请打开保存的 _topview_XY.png / _topview_XZ.png / _topview_YZ.png，\n"
        "确认ArUco标记是否清晰可见（黑白方格图案）。\n"
        "常见原因：\n"
        "  1. 重建时未启用顶点颜色（-calculateVertexColors）\n"
        "  2. 点云采样太稀疏（dataset 中采样数 number_of_points 太小）\n"
        "  3. ArUco字典不对（修改 ARUCO_DICT_NAME）\n"
        "  4. 增大分辨率：TOPVIEW_IMG_PX = 4000"
    )

print(f"检测到 {len(ids)} 个标记，ID = {ids.flatten()}")

# 取第一个标记计算尺度（多标记时取平均）
all_scales = []
for corner in corners:
    c = corner[0]  # shape (4, 2) 像素坐标
    side_px = [np.linalg.norm(c[(i+1) % 4] - c[i]) for i in range(4)]
    marker_size_ply = np.mean(side_px) / ppu  # 换算为PLY坐标单位
    scale = ARUCO_MARKER_SIZE_M / marker_size_ply
    all_scales.append(scale)

scale_factor = float(np.mean(all_scales))

print(f"\n各标记缩放因子: {[round(s, 5) for s in all_scales]}")
print(f"最终缩放因子 (平均值): {scale_factor:.5f}")
print(f"含义: PLY单位 × {scale_factor:.4f} = 米")

# 保存可视化（俯视图 + 标记框）
vis = img.copy()
aruco.drawDetectedMarkers(vis, corners, ids)
vis_path = ply_path.replace(".ply", "_aruco_topview.png")
cv2.imwrite(vis_path, cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
print(f"\n可视化已保存: {vis_path}")

# 保存缩放因子到同目录的txt文件，供后续步骤读取
scale_txt_path = ply_path.replace(".ply", "_scale.txt")
with open(scale_txt_path, "w") as f:
    f.write(str(scale_factor))
print(f"缩放因子已保存: {scale_txt_path}")

print("\n尺度校准完成！")