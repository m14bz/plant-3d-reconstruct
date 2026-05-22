        # Main.py - 3D重建自动化流程文档

## 概述

这是一个自动化的3D重建流程脚本，用于批量处理图像并生成3D模型。整个流程包括项目创建、前景提取、三维重建和三维预处理四个主要步骤。

## 功能模块

### 1. 配置参数（第9-15行）

```python
base_url = r"images"                    # 原始图像存放目录
output_url = r"output"                  # 输出结果目录
dataset_url = r"dataset"                # 最终数据集目录
realityCapture_url = r"..."             # RealityCapture软件路径
realityCapture_params_url = r"params.xml"  # 重建参数配置文件
img_num = 150                           # 每个项目包含的图像数量
```

**参数说明：**
- `base_url`: 存放待处理JPG图像的源目录
- `output_url`: 中间处理结果和项目文件的输出目录
- `dataset_url`: 最终处理完成的点云数据存放目录
- `realityCapture_url`: RealityCapture软件的可执行文件路径
- `realityCapture_params_url`: 3D重建的参数配置XML文件
- `img_num`: 控制每个项目包含的图像数量（每150张图像创建一个新项目）

### 2. 创建项目（第17-41行）

**功能：** 根据图像数量自动创建项目文件夹结构，并将原始图像分配到对应项目中

**处理流程：**
1. 遍历`images`目录下的所有JPG文件
2. 每150张图像创建一个新的项目文件夹
3. 为每个项目创建以下子目录：
   - `labels/`: 存放3D模型输出文件
   - `project/`: 存放RealityCapture项目文件
   - `original/`: 存放原始图像副本
   - `fore/`: 存放前景提取后的图像
4. 将图像复制到对应项目的`original`目录

**文件命名规则：** 脚本从图像文件名中提取项目名称，格式为`*_项目名_*.JPG`

### 3. 前景提取（第43-52行）

**功能：** 使用rembg工具移除图像背景，提取前景对象

**技术细节：**
- 使用模型：`birefnet-general`
- 模型路径：`C:\Users\cdh96\.u2net\birefnet-general.onnx`
- 处理方式：批量处理模式（`rembg p`）
- 输入：`original`目录下的图像
- 输出：`fore`目录下的透明背景图像

**命令参数说明：**
```bash
rembg p                          # 批量处理模式
-m birefnet-general              # 使用birefnet-general模型
-x "{\"model_path\": \"...\"}"   # 指定模型文件路径
[输入目录]                        # 原始图像目录
[输出目录]                        # 前景图像输出目录
```

### 4. 三维重建（第54-69行）

**功能：** 使用RealityCapture软件对前景图像进行3D重建

**重建流程：**
1. 添加前景图像文件夹（`-addFolder`）
2. 对齐图像（`-align`）
3. 合并组件（`-mergeComponents`）
4. 自动设置重建区域（`-setReconstructionRegionAuto`）
5. 计算高精度模型（`-calculateHighModel`）
6. 计算顶点颜色（`-calculateVertexColors`）
7. 计算纹理（`-calculateTexture`）
8. 导出模型为PLY格式（`-exportModel`）
9. 保存项目文件（`-save`）
10. 退出软件（`-quit`）

**输出文件：**
- 3D模型：`labels/{项目名}.ply`
- 项目文件：`project/{项目名}.rcproj`

### 5. 三维预处理（第71-86行）

**功能：** 使用Open3D对生成的3D模型进行后处理，生成清洁的点云数据

**处理步骤：**
1. 读取OBJ格式的三维网格模型
2. 均匀采样10000个点
3. 使用半径滤波去除离群点
   - 最少邻近点数：3
   - 搜索半径：0.05
4. 将处理后的点云保存为PLY格式到`dataset`目录

**参数调整建议：**
- `number_of_points`: 根据模型复杂度调整采样点数
- `nb_points`: 增加此值可以更严格地过滤离群点
- `radius`: 根据模型尺度调整搜索半径

## 依赖项

### Python库
```bash
pip install glob
pip install tqdm
pip install pathlib
pip install open3d
pip install rembg
```

### 外部软件
- **RealityCapture**: 商业3D重建软件
  - 安装路径：`C:\Program Files\Capturing Reality\RealityCapture\RealityCapture.exe`
  - 需要有效的许可证

### 模型文件
- **BiRefNet模型**: `birefnet-general.onnx`
  - 默认路径：`C:\Users\cdh96\.u2net\birefnet-general.onnx`
  - 可通过rembg自动下载

## 使用方法

### 1. 准备工作

1. 将待处理的JPG图像放入`images`目录
2. 确保图像命名格式为：`*_项目标识_*.JPG`
3. 准备RealityCapture参数配置文件`params.xml`
4. 安装所有必需的依赖项和软件

### 2. 配置参数

根据实际环境修改main.py中的配置参数：
- 调整文件路径
- 设置每个项目的图像数量
- 配置RealityCapture路径

### 3. 运行脚本

```bash
python main.py
```

或使用Jupyter Notebook：
```bash
jupyter notebook main.ipynb
```

### 4. 输出结果

- **中间结果**：`output/{项目名}/`
  - `original/`: 原始图像
  - `fore/`: 前景提取图像
  - `labels/`: 3D模型文件
  - `project/`: RealityCapture项目文件

- **最终结果**：`dataset/`
  - 清洁的点云PLY文件

## 注意事项

1. **存储空间**: 确保有足够的磁盘空间，3D重建过程会生成大量中间文件
2. **处理时间**: 前景提取和3D重建非常耗时，300张图像可能需要数小时
3. **图像质量**: 输入图像质量直接影响重建效果，建议使用高分辨率图像
4. **内存要求**: Open3D和RealityCapture需要较大内存，建议16GB以上
5. **路径问题**:
   - 所有路径建议使用绝对路径
   - Windows路径使用原始字符串（r"..."）避免转义问题
6. **错误处理**: 当前版本未包含完整的错误处理，建议在生产环境中添加异常捕获

## 性能优化建议

1. **并行处理**: 前景提取和3D重建可以并行处理多个项目
2. **GPU加速**:
   - rembg支持GPU加速
   - RealityCapture可使用GPU加速重建
3. **批处理**: 合理设置`img_num`参数，避免单个项目图像过多导致内存溢出
4. **中间文件清理**: 定期清理不需要的中间文件释放空间

## 扩展功能建议

1. 添加命令行参数支持
2. 实现断点续传功能
3. 添加日志记录系统
4. 实现多进程/多线程并行处理
5. 添加质量检查和验证步骤
6. 支持更多输入输出格式

## 版本信息

- **Python版本**: 3.7+
- **主要依赖版本**:
  - Open3D: 最新稳定版
  - rembg: 支持birefnet-general模型的版本
  - tqdm: 最新版本

## 联系方式

如有问题或建议，请联系开发者。
