# 图片拼图工具

## 功能描述

本脚本用于批量处理图片拼图任务，自动遍历指定目录下的图片文件夹，将成对的图片按照特定规则拼接成新的图片。

## 快速开始

### 方式一：使用 Makefile（推荐）

```bash
# 1. 首次使用：创建虚拟环境并安装依赖
make install    # 创建虚拟环境
make setup      # 安装依赖

# 2. 运行脚本
make run

# 3. 带参数运行
make run ARGS="--main-color #ffffff"  # 使用纯色背景
make run ARGS="--main-color"           # 自动提取主色调
```

### 方式二：使用启动脚本（最简单）

```bash
# 直接运行启动脚本（会自动创建虚拟环境和安装依赖）
./start.sh                    # 使用默认背景
./start.sh --main-color #fff  # 使用纯色背景
./start.sh --main-color       # 自动提取主色调
```

### 方式三：手动激活虚拟环境

```bash
# 1. 创建并激活虚拟环境
make install
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate      # Windows

# 2. 安装依赖（如果还没安装）
make setup
# 或手动安装
pip install Pillow numpy scikit-learn

# 3. 运行脚本
python puzzle.py                    # 使用默认背景
python puzzle.py --main-color #fff  # 使用纯色背景
python puzzle.py --main-color       # 自动提取主色调

# 4. 退出虚拟环境
deactivate
```

### 查看可用命令

```bash
make help      # 查看所有可用命令
make activate  # 查看激活虚拟环境的命令
```

## 环境要求

- Python 3.x（推荐 3.8+，系统已安装）
- virtualenv（用于创建虚拟环境，Makefile 会自动安装）
- 使用 Makefile 进行虚拟环境创建和脚本执行
- 依赖包：Pillow, numpy, scikit-learn（通过 Makefile 自动安装）

### 安装 virtualenv（如需要）

如果遇到虚拟环境创建失败，可以手动安装 virtualenv：

```bash
# 使用 pip 安装（推荐）
pip install virtualenv
# 或
python3 -m pip install virtualenv

# 或使用系统包管理器（Ubuntu/Debian）
sudo apt install python3-virtualenv

# 安装完成后
make clean
make install
```

**注意**：Makefile 会自动检查并安装 virtualenv，通常不需要手动安装。

## 目录结构

```
backend/
└── cover/
    ├── back.jpg                # 默认底图
    ├── mobile-block-cover.png  # Mobile 覆盖图
    ├── pad-block-cover.png     # Pad 覆盖图
    ├── pad-lock-cover.png     # Pad 锁定覆盖图
    ├── pc-mac-cover.png        # PC Mac 覆盖图
    ├── imgs/                    # 图片根目录
    │   └── example/            # 示例图片目录（实际为具体项目目录）
    │       ├── mobile-desktop.png
    │       ├── mobile-lock.png
    │       ├── pc.png
    │       ├── pc-block.png
    │       ├── pad-desktop.png
    │       └── pad-lock.png
    ├── puzzle.py               # 拼图脚本
    ├── Makefile                # 构建脚本
    ├── start.sh                # 启动脚本（可选）
    └── README.md               # 本文件
```

## 功能需求

### 1. 目录遍历

脚本每次执行时都会遍历 `imgs` 目录下的所有子目录，对每个子目录进行以下处理：

### 2. 处理逻辑

#### 2.1 跳过已处理目录
- 如果子目录下已存在 `intr` 文件夹，则跳过该目录，不进行处理

#### 2.2 文件完整性检查
- 检查目录下是否包含以下 6 个图片文件：
  - `mobile.png` 和 `mobile-lock.png`（成对）
  - `pc.png` 和 `pc-block.png`（成对）
  - `pad.png`
- 如果缺少成对的图片文件（例如缺少 `mobile.png` 和 `mobile-lock.png`），则：
  - 输出目录路径和错误信息
  - 继续处理下一个目录

#### 2.3 拼图处理

当文件完整性检查通过后，执行以下拼图逻辑：

1. **创建输出目录**
   - 在处理的目录下创建 `intr` 文件夹

2. **准备工作**（图片预处理）

   在拼接图片之前，需要先进行图片预处理，生成所需的中间图片：

   **a) Mobile 图片预处理**
   - 检查当前目录下是否存在 `mobile-desktop.png`
   - 若不存在，执行以下操作：
     - 将 `mobile-block-cover.png` 和 `mobile.png` 做重合处理
     - `mobile.png` 作为底图，`mobile-block-cover.png` 覆盖在底图上
     - 两张图片都是 9:19 比例
     - 生成的新图保存为 `mobile-desktop.png`

   **b) Pad 图片预处理**
   - 检查当前目录下是否存在 `pad-desktop.png` 和 `pad-lock.png`
   - 若 `pad-desktop.png` 不存在，执行以下操作：
     - 将 `pad-block-cover.png` 和 `pad.png` 做重合处理
     - `pad.png` 作为底图，`pad-block-cover.png` 覆盖在底图上
     - 两张图片都是 4:3 比例
     - 生成的新图保存为 `pad-desktop.png`
   - 若 `pad-lock.png` 不存在，执行以下操作：
     - 将 `pad-lock-cover.png` 和 `pad.png` 做重合处理
     - `pad.png` 作为底图，`pad-lock-cover.png` 覆盖在底图上
     - 两张图片都是 4:3 比例
     - 生成的新图保存为 `pad-lock.png`

   **c) PC 图片预处理**
   - 检查当前目录下是否存在 `pc-desktop-mac.png`
   - 若不存在，执行以下操作：
     - 将 `pc-mac-cover.png` 和 `pc.png` 做重合处理
     - `pc.png` 作为底图，`pc-mac-cover.png` 覆盖在底图上
     - 两张图片都是 16:9 比例
     - 生成的新图保存为 `pc-desktop-mac.png`

3. **背景处理**
   - 默认使用 `back.jpg` 作为所有拼图的底图
   - 支持 `--main-color` 参数：
     - 如果提供 16 进制色号（如 `#fff`），使用该颜色作为纯色背景
     - 如果不提供色号，自动提取图片中的主色调作为背景色

4. **拼图规则**

   **a) Mobile 拼图**（`mobile-lock.png` + `mobile-desktop.png`）
   - 横向排列两张图片
   - 图片之间留有间隔
   - 每张图片独立添加边框阴影和圆角效果
   - **原始图片比例**：输入图片为 9:19 比例（像素尺寸可能有差异，但比例不变）
   - **最终结果**：1:1 比例，大小不超过 2MB

   **b) PC 拼图**（`pc-block.png` + `pc-desktop-mac.png`）
   - 纵向排列两张图片
   - 图片之间留有间隔
   - 每张图片独立添加边框阴影和圆角效果
   - **原始图片比例**：输入图片为 16:9 比例（像素尺寸可能有差异，但比例不变）
   - **最终结果**：1:1 比例，大小不超过 2MB
   - **特殊情况**：如果只存在其中一张图片，则将该图居中显示

   **c) Pad 拼图**（`pad-lock.png` + `pad-desktop.png`）
   - 横向排列两张图片
   - 图片之间留有间隔
   - 每张图片独立添加边框阴影和圆角效果
   - **原始图片比例**：输入图片为 4:3 比例（像素尺寸可能有差异，但比例不变）
   - **最终结果**：1:1 比例，大小不超过 2MB

## 技术实现要点

### 依赖库（建议）
- `Pillow` (PIL) - 图片处理
- `numpy` - 数值计算（用于主色调提取）
- `scikit-image` 或 `opencv-python` - 图像处理（可选，用于高级功能）

### 关键功能点

1. **主色调提取**
   - 使用 K-means 聚类或直方图分析提取图片主色调
   - 考虑图片边缘和背景区域

2. **图片拼接**
   - 计算合适的图片尺寸和间距
   - **输入图片比例**（原始图片保持各自比例）：
     - Mobile 拼图输入：9:19
     - PC 拼图输入：16:9
     - Pad 拼图输入：4:3
   - **输出图片比例**：所有拼图结果统一为 1:1 比例
   - 处理不同尺寸的输入图片（可能需要缩放和适配）
   - **重要**：输入图片的像素尺寸可能有差异，但必须保持各自指定的原始宽高比，最终拼图结果统一调整为 1:1 比例

3. **视觉效果**
   - 阴影效果：使用 Pillow 的 ImageFilter 或手动绘制
   - 圆角效果：使用遮罩或路径裁剪
   - 边框：可选的边框样式

4. **文件大小控制**
   - 如果生成的图片超过 2MB，需要调整质量参数或尺寸
   - 使用适当的图片格式（PNG/JPG）和压缩参数

5. **错误处理**
   - 文件不存在、格式不支持、处理失败等情况
   - 记录详细的错误日志

## 补充建议

### 1. 配置化
- 支持配置文件（如 `config.json`）定义：
  - 默认间隔大小
  - 阴影参数（偏移、模糊、颜色）
  - 圆角半径
  - 输出图片质量
  - 文件大小限制

### 2. 日志系统
- 添加日志记录功能，记录：
  - 处理的目录列表
  - 跳过的目录及原因
  - 错误信息
  - 处理进度

### 3. 进度显示
- 显示处理进度（当前目录/总目录数）
- 预估剩余时间

### 4. 图片格式支持
- 支持多种图片格式（PNG, JPG, JPEG, WEBP 等）
- 自动识别图片格式

### 5. 输出文件命名
- 明确输出文件的命名规则（如 `mobile-combined.png`, `pc-combined.png`, `pad-combined.png`）
- 或使用时间戳/哈希值避免覆盖

### 6. 参数验证
- 验证 `--main-color` 参数格式（16 进制颜色代码）
- 验证输入路径是否存在
- 验证图片文件是否可读

### 7. 性能优化
- 对于大量目录，考虑并行处理
- 图片缓存机制
- 内存管理（处理大图片时）

### 8. 测试用例
- 准备测试数据（包含各种情况的目录）
- 单元测试和集成测试

### 9. 文档完善
- 命令行参数说明
- 使用示例
- 常见问题解答

### 10. 异常情况处理
- 图片损坏无法读取
- 图片尺寸异常（过大或过小）
- 内存不足
- 磁盘空间不足

## Makefile 功能

Makefile 包含以下目标：

- `install` - 创建 Python 虚拟环境（如果不存在）
- `setup` - 安装项目依赖（会自动创建虚拟环境）
- `run` - 执行拼图脚本（会自动安装依赖）
- `clean` - 清理临时文件和虚拟环境
- `test` - 运行测试（如果实现）
- `activate` - 显示激活虚拟环境的命令

## 使用示例

```bash
# 首次使用：创建虚拟环境并安装依赖
make install
make setup

# 或者直接运行（会自动执行 install 和 setup）
make run

# 使用纯色背景
make run ARGS="--main-color #ffffff"

# 使用主色调背景（自动提取）
make run ARGS="--main-color"

# 手动激活虚拟环境（如果需要直接运行脚本）
make activate
# 然后运行显示的命令，例如：
# source venv/bin/activate
# python puzzle.py --main-color #fff
```
