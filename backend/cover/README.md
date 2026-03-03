# 图片拼图工具

## 功能描述

本脚本用于批量处理图片拼图任务，自动遍历 `imgs` 目录下的项目目录，对每个项目下的子目录中的图片按照特定规则拼接，结果输出到对应的 `*-result` 目录。

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
pip install Pillow numpy scikit-learn scipy

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
- 依赖包：Pillow, numpy, scikit-learn, scipy（通过 Makefile 自动安装）

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
    ├── back.png                # 默认底图（3:4 比例）
    ├── mobile-block-cover.png  # Mobile 覆盖图
    ├── pad-block-cover.png     # Pad 覆盖图
    ├── pad-lock-cover.png      # Pad 锁定覆盖图
    ├── pc-mac-cover.png        # PC Mac 覆盖图
    ├── phone_template.png      # 手机模板图（用于 phone_screen_replace）
    ├── imgs/                   # 图片根目录
    │   ├── projectA/           # 项目目录（如 "you and me"）
    │   │   ├── 1/              # 子目录（一组图片）
    │   │   │   ├── mobile.png
    │   │   │   ├── mobile-lock.png
    │   │   │   ├── pc.png      # 可选
    │   │   │   └── pad.png     # 可选
    │   │   └── 2/
    │   │       ├── mobile.png
    │   │       └── mobile-lock.png
    │   └── projectA-result/    # 自动生成的结果目录（若已存在则跳过整个项目）
    │       ├── 1/
    │       │   ├── mobile-cover.png      # phone mockup 结果
    │       │   ├── mobile-desktop.png    # 中间文件
    │       │   ├── mobile-combined.jpg   # Mobile 拼图结果
    │       │   ├── mobile-combined-2.jpg # Mobile 拼图结果（磨玻璃版）
    │       │   ├── pc-desktop-mac.png    # 中间文件（若有 pc.png）
    │       │   ├── pc-combined.jpg       # PC 拼图结果（若有 pc.png）
    │       │   ├── pad-desktop.png       # 中间文件（若有 pad.png）
    │       │   ├── pad-lock.png          # 中间文件（若有 pad.png）
    │       │   └── pad-combined.jpg      # Pad 拼图结果（若有 pad.png）
    │       └── 2/
    │           └── ...
    ├── puzzle.py               # 拼图脚本（主入口）
    ├── mobile_puzzle.py        # Mobile 拼图模块
    ├── pad_puzzle.py           # Pad 拼图模块
    ├── pc_puzzle.py            # PC 拼图模块
    ├── phone_screen_replace.py # 手机屏幕替换工具
    ├── utils.py                # 公共工具函数
    ├── Makefile                # 构建脚本
    ├── start.sh                # 启动脚本（可选）
    └── README.md               # 本文件
```

## 功能需求

### 1. 目录遍历

脚本每次执行时会遍历 `imgs` 目录下的所有**一级子目录**（即项目目录），对每个项目进行处理：

### 2. 处理逻辑

#### 2.1 跳过已处理项目
- 若 `imgs/projectA-result/` 目录已存在，则跳过整个 `projectA` 项目，不进行任何处理

#### 2.2 子目录遍历
- 遍历 `imgs/projectA/` 下的所有子目录（如 `1/`、`2/` 等）
- 每个子目录独立处理，结果输出至 `imgs/projectA-result/<子目录名>/`

#### 2.3 处理方式

`imgs/projectA/` 下支持两种处理方式，可同时存在：

**方式一：子目录（文件夹）**
遍历每个子目录（如 `1/`、`2/`），独立处理，结果输出至 `projectA-result/<子目录名>/`。

**方式二：直接图片文件（成对命名）**
若项目根目录下直接存放了成对图片（`{name}.*` + `{name}-lock.*`），则批量处理每对：
- `{name}-lock.*` → phone_screen_replace → `projectA-result/{name}-cover.png`
- `{name}.*` + mobile-block-cover.png → overlay → `projectA-result/{name}-desktop.png`
- `{name}-lock.*` + `{name}-desktop.png` → 横向拼图 → `projectA-result/{name}-combined.jpg`

例如存在 `1.png` + `1-lock.png`、`2.png` + `2-lock.jpg`，会生成 `1-cover.png`、`1-desktop.png`、`1-combined.jpg` 等。

---

#### 2.4 子目录内图片处理逻辑

对每个子目录，根据其中存在的文件按以下规则处理：

**a) 手机屏幕替换**（`mobile-lock.*`）
- 检查是否存在 `mobile-lock.png`（支持 jpg/jpeg/webp 等格式）
- 若存在，使用 `phone_screen_replace.py` 将 `mobile-lock.*` 作为壁纸替换到 `phone_template.png` 的屏幕区域
- 生成结果保存为 `mobile-cover.png`（放到结果子目录）

**b) Mobile 图片预处理**（`mobile.png`）
- 检查是否存在 `mobile.png`
- 若存在且结果目录中不存在 `mobile-desktop.png`，执行以下操作：
  - 将 `mobile-block-cover.png` 和 `mobile.png` 做重合处理
  - `mobile.png` 作为底图，`mobile-block-cover.png` 覆盖在底图上
  - 两张图片都是 9:19 比例
  - 生成的新图保存为 `mobile-desktop.png`（放到结果子目录）
- 同理生成 `mobile-desktop-2.png`（磨玻璃效果版本）

**c) Mobile 拼图**（`mobile-lock.*` + `mobile-desktop.png`）
- 同时存在 `mobile-lock.*`（源目录）和 `mobile-desktop.png`（结果目录中间文件）时执行
- 横向排列两张图片
- 图片之间留有间隔
- 每张图片独立添加边框阴影和圆角效果
- **原始图片比例**：输入图片为 9:19 比例（像素尺寸可能有差异，但比例不变）
- **最终结果**：3:4 比例，大小不超过 2MB，结果居中显示

**d) Pad 图片预处理**（`pad.png`）
- 检查是否存在 `pad.png`
- 若 `pad-desktop.png` 不存在于结果目录，执行以下操作：
  - 将 `pad-block-cover.png` 和 `pad.png` 做重合处理
  - `pad.png` 作为底图，`pad-block-cover.png` 覆盖在底图上
  - 两张图片都是 4:3 比例
  - 生成的新图保存为 `pad-desktop.png`
- 若 `pad-lock.png` 不存在于结果目录，执行以下操作：
  - 将 `pad-lock-cover.png` 和 `pad.png` 做重合处理
  - `pad.png` 作为底图，`pad-lock-cover.png` 覆盖在底图上
  - 两张图片都是 4:3 比例
  - 生成的新图保存为 `pad-lock.png`

**e) PC 图片预处理**（`pc.png`）
- 检查是否存在 `pc.png`
- 若 `pc-desktop-mac.png` 不存在于结果目录，执行以下操作：
  - 将 `pc-mac-cover.png` 和 `pc.png` 做重合处理
  - `pc.png` 作为底图，`pc-mac-cover.png` 覆盖在底图上
  - 两张图片都是 16:9 比例
  - 生成的新图保存为 `pc-desktop-mac.png`

**f) PC 拼图**（`pc.png` + `pc-desktop-mac.png`）
- 纵向排列两张图片
- 图片之间留有间隔
- 每张图片独立添加边框阴影和圆角效果
- **原始图片比例**：输入图片为 16:9 比例（像素尺寸可能有差异，但比例不变）
- **最终结果**：3:4 比例，大小不超过 2MB，结果居中显示
- **特殊情况**：如果只存在其中一张图片，则将该图居中显示

**g) Pad 拼图**（`pad-lock.png` + `pad-desktop.png`）
- 横向排列两张图片
- 图片之间留有间隔
- 每张图片独立添加边框阴影和圆角效果
- **原始图片比例**：输入图片为 4:3 比例（像素尺寸可能有差异，但比例不变）
- **最终结果**：3:4 比例，大小不超过 2MB，结果居中显示

### 3. 背景处理
- 默认使用 `back.png`（3:4 比例）作为所有拼图的底图
- 支持 `--main-color` 参数：
  - 如果提供 16 进制色号（如 `#fff`），使用该颜色作为纯色背景
  - 如果不提供色号，自动提取图片中的主色调作为背景色

## 技术实现要点

### 依赖库
- `Pillow` (PIL) - 图片处理
- `numpy` - 数值计算（用于主色调提取）
- `scikit-learn` - K-means 聚类（主色调提取）
- `scipy` - 图像处理（用于 phone_screen_replace）

### 关键功能点

1. **手机屏幕替换**（phone_screen_replace.py）
   - 自动检测 phone_template.png 中的白色屏幕区域
   - 将壁纸以 cover 模式填充到屏幕区域
   - 边缘使用亮度渐变 alpha 混合，无白边
   - 输出保持原图分辨率，无损 PNG

2. **主色调提取**
   - 使用 K-means 聚类提取图片主色调

3. **图片拼接**
   - **输入图片比例**（原始图片保持各自比例）：
     - Mobile 拼图输入：9:19
     - PC 拼图输入：16:9
     - Pad 拼图输入：4:3
   - **输出图片比例**：所有拼图结果统一为 3:4 比例（与 back.png 一致）
   - 拼图内容在 3:4 画布中居中显示

4. **视觉效果**
   - 阴影效果：使用 Pillow 的 ImageFilter 绘制高斯阴影
   - 圆角效果：使用遮罩裁剪
   - 边框：可选的边框样式

5. **文件大小控制**
   - 如果生成的图片超过 2MB，自动调整质量参数
   - 最终输出统一压缩至 200-300KB

6. **错误处理**
   - 文件不存在、格式不支持、处理失败等情况均有日志记录
   - 单个子目录失败不影响其他子目录继续处理

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

## 典型使用场景

```
# 假设有如下目录结构：
imgs/
└── summer-2024/
    ├── 1/
    │   ├── mobile.png
    │   └── mobile-lock.png
    └── 2/
        ├── mobile.png
        ├── mobile-lock.jpg
        ├── pc.png
        └── pad.png

# 执行 make run 后，自动生成：
imgs/
├── summer-2024/          ← 原始目录，不变
└── summer-2024-result/   ← 自动生成
    ├── 1/
    │   ├── mobile-cover.png      ← 手机屏幕替换结果
    │   ├── mobile-desktop.png    ← Mobile 预处理中间文件
    │   ├── mobile-desktop-2.png  ← Mobile 磨玻璃预处理中间文件
    │   ├── mobile-combined.jpg   ← Mobile 拼图
    │   └── mobile-combined-2.jpg ← Mobile 磨玻璃拼图
    └── 2/
        ├── mobile-cover.png
        ├── mobile-desktop.png
        ├── mobile-desktop-2.png
        ├── mobile-combined.jpg
        ├── mobile-combined-2.jpg
        ├── pc-desktop-mac.png    ← PC 预处理中间文件
        ├── pc-combined.jpg       ← PC 拼图
        ├── pad-desktop.png       ← Pad 预处理中间文件
        ├── pad-lock.png          ← Pad 预处理中间文件
        └── pad-combined.jpg      ← Pad 拼图

# 再次执行 make run 时，summer-2024-result 已存在，自动跳过 summer-2024 项目
```
