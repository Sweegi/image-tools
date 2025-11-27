# Image Tools - 图片处理工具集

一个集成了多种图片处理功能的工具集，包含后端批量处理工具和前端可视化工具，支持图片拼图、切分、星星点位绘制等功能。

## 📋 项目概述

本项目提供了一套完整的图片处理解决方案，分为后端批量处理工具和前端可视化工具两部分：

- **后端工具**：基于 Python 的批量图片处理脚本，支持命令行操作
- **前端工具**：基于 Vue3 的 Web 应用，提供可视化的图片编辑和绘制功能

## ✨ 功能特性

### 后端工具 (Backend)

#### 1. 图片拼图工具 (`backend/cover/`)
- ✅ **多设备支持**：支持 Mobile、PC、Pad 三种设备的拼图生成
- ✅ **批量处理**：自动遍历目录，批量处理多组图片
- ✅ **智能布局**：根据设备类型自动调整图片排列方式
- ✅ **样式优化**：自动添加边框、阴影、圆角等视觉效果
- ✅ **背景处理**：支持纯色背景、自动提取主色调、使用默认底图
- ✅ **文件优化**：自动压缩图片大小，确保输出文件不超过 2MB
- ✅ **输出格式**：统一输出为 1:1 比例的 JPG 格式

**支持的拼图类型**：
- **Mobile 拼图**：将锁屏图和桌面图拼接（输入 9:19，输出 1:1）
- **PC 拼图**：将锁屏图和桌面图拼接（输入 16:9，输出 1:1）
- **Pad 拼图**：将锁屏图和桌面图拼接（输入 4:3，输出 1:1）

#### 2. 图片切分工具 (`backend/split/`)
- ✅ **四格切分**：将 2x2 四格图片切分成四张独立图片
- ✅ **批量处理**：自动处理目录下所有 PNG 文件
- ✅ **自动命名**：按左上、右上、左下、右下顺序自动命名

### 前端工具 (Web)

#### 1. 星星点位绘制工具 (`/star-pattern`)
- ✅ **背景管理**：支持上传本地图片、纯色背景、网格背景
- ✅ **数据导入**：支持 JSON 格式的星星点位数据导入（相对坐标/绝对坐标）
- ✅ **星星绘制**：根据点位数据自动绘制星星并连接
- ✅ **交互操作**：支持整体拖拽、缩放、旋转，实时更新连线
- ✅ **样式定制**：可自定义星星样式（大小、颜色、描边、阴影）和连线样式
- ✅ **导出功能**：支持导出为 PNG/JPG，支持多倍分辨率（2x、3x、4x）

#### 2. 拼图工具 (`/puzzle-pattern`)
- 🚧 开发中

## 🏗️ 项目结构

```
image-tools/
├── backend/                    # 后端工具目录
│   ├── cover/                 # 图片拼图工具
│   │   ├── puzzle.py          # 主入口脚本
│   │   ├── mobile_puzzle.py   # Mobile 拼图实现
│   │   ├── pc_puzzle.py       # PC 拼图实现
│   │   ├── pad_puzzle.py      # Pad 拼图实现
│   │   ├── utils.py           # 工具函数
│   │   ├── README.md          # 详细使用文档
│   │   └── imgs/              # 图片输入目录（gitignore）
│   └── split/                 # 图片切分工具
│       ├── split_images.py    # 切分脚本
│       ├── README.md          # 使用文档
│       └── imgs/              # 图片输入目录（gitignore）
│
├── web/                       # 前端应用目录
│   ├── src/
│   │   ├── components/        # 组件
│   │   │   ├── CanvasComponent.vue    # 画布组件
│   │   │   └── Layout/        # 布局组件
│   │   ├── views/             # 页面视图
│   │   │   ├── star/          # 星星点位绘制页面
│   │   │   └── puzzle/        # 拼图页面
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── router/            # 路由配置
│   │   └── App.vue            # 根组件
│   ├── package.json           # 依赖配置
│   └── README.md              # 前端文档
│
├── Makefile                   # 后端构建脚本
├── start.sh                   # 后端启动脚本
└── README.md                  # 项目总览（本文件）
```

## 🚀 快速开始

### 后端工具

#### 方式一：使用启动脚本（推荐）

```bash
# 直接运行启动脚本（会自动创建虚拟环境和安装依赖）
./start.sh                    # 使用默认背景
./start.sh --main-color #fff  # 使用纯色背景
./start.sh --main-color       # 自动提取主色调
```

#### 方式二：使用 Makefile

```bash
# 1. 首次使用：创建虚拟环境并安装依赖
make install    # 创建虚拟环境
make setup      # 安装依赖

# 2. 运行拼图脚本
cd backend/cover
make run

# 3. 运行切分脚本
cd backend/split
python split_images.py
```

#### 方式三：手动操作

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install Pillow numpy scikit-learn

# 3. 运行脚本
cd backend/cover
python puzzle.py
```

### 前端工具

```bash
# 1. 进入前端目录
cd web

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 构建生产版本
npm run build
```

## 📖 详细使用说明

### 后端 - 图片拼图工具

#### 准备工作

1. 在 `backend/cover/imgs/` 目录下创建子目录（如 `my-project/`）
2. 在子目录中放置图片文件：
   - `mobile-lock.png` / `mobile-lock.jpg` - Mobile 锁屏图
   - `mobile.png` / `mobile.jpg` - Mobile 桌面图
   - `pc-block.png` / `pc-block.jpg` - PC 锁屏图
   - `pc.png` / `pc.jpg` - PC 桌面图
   - `pad.png` / `pad.jpg` - Pad 桌面图

#### 运行处理

```bash
cd backend/cover
./start.sh
```

处理完成后，结果会保存在各子目录的 `intr/` 目录下：
- `mobile-combined.jpg` - Mobile 拼图结果
- `pc-combined.jpg` - PC 拼图结果
- `pad-combined.jpg` - Pad 拼图结果

#### 参数说明

- `--main-color #ffffff`：使用指定的纯色背景
- `--main-color`：自动提取图片主色调作为背景色
- 无参数：使用默认底图 `back.jpg`

### 后端 - 图片切分工具

#### 使用方法

1. 将要切分的四格 PNG 图片放入 `backend/split/imgs/` 目录
2. 运行脚本：
   ```bash
   cd backend/split
   python split_images.py
   ```
3. 切分后的图片会保存在 `new-imgs/` 目录

#### 输出命名规则

- 原文件：`example.png`
- 切分后：
  - `example_1.png` - 左上角
  - `example_2.png` - 右上角
  - `example_3.png` - 左下角
  - `example_4.png` - 右下角

### 前端 - 星星点位绘制工具

#### 基本使用流程

1. **设置画布**
   - 选择画布比例（9:16、3:4、1:1、自适应）
   - 选择背景类型（网格/图片/纯色）

2. **导入数据**
   - 在左侧栏输入 JSON 格式的星星点位数据
   - 点击"生成星星"按钮

3. **调整样式**
   - 在右侧栏调整星星和连线的样式

4. **操作星星组**
   - 点击星星显示操作框
   - 拖拽、缩放、旋转星星组

5. **导出图片**
   - 点击右上角"导出图片"按钮
   - 选择格式和分辨率

#### 数据格式示例

```json
{
  "points": [
    {"id": 1, "x": 0.21, "y": 0.25},
    {"id": 2, "x": 0.2838, "y": 0.2817},
    {"id": 3, "x": 0.1, "y": 0.4428}
  ],
  "connections": [[1, 2], [2, 3]]
}
```

更多详细说明请参考：
- [后端拼图工具文档](./backend/cover/README.md)
- [后端切分工具文档](./backend/split/README.md)
- [前端应用文档](./web/README.md)

## 🛠️ 技术栈

### 后端
- **Python 3.8+**
- **Pillow** - 图片处理
- **NumPy** - 数值计算
- **scikit-learn** - 颜色提取（KMeans）

### 前端
- **Vue 3** - 前端框架
- **Vite** - 构建工具
- **Konva** - 2D 画布库
- **Element Plus** - UI 组件库
- **TailwindCSS** - CSS 框架
- **Pinia** - 状态管理
- **Vue Router** - 路由管理

## 📝 开发说明

### 环境要求

**后端**：
- Python 3.8+
- virtualenv（可选，Makefile 会自动安装）

**前端**：
- Node.js 16+
- npm 或 yarn

### 开发流程

1. **后端开发**
   ```bash
   # 创建虚拟环境
   make install
   
   # 安装依赖
   make setup
   
   # 激活虚拟环境
   source venv/bin/activate
   
   # 运行脚本
   cd backend/cover
   python puzzle.py
   ```

2. **前端开发**
   ```bash
   cd web
   npm install
   npm run dev
   ```

### 代码规范

- Python 代码遵循 PEP 8 规范
- JavaScript/Vue 代码遵循 ESLint 规范
- 使用简体中文编写注释和文档

## 📄 许可证

MIT License

Copyright (c) 2025 Sweegi

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题或建议，请通过 Issue 反馈。
