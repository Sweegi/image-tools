# 星星点位绘制工具 - 需求文档

> 本文档详细描述了星星点位绘制工具的功能设计、技术实现和交互流程。
> 项目概述、安装部署和使用说明请参考 [README.md](./README.md)

## 一、核心功能需求

### 1.1 基础功能

#### 1.1.1 背景图片管理
- **功能描述**：用户可以为画布设置背景图片
- **实现方式**：
  - 支持上传本地图片文件（JPG、PNG格式）
  - 支持设置纯色背景（颜色选择器）
  - 背景图片自动适配画布大小
  - 默认背景：白色底 + 灰色网格图案

#### 1.1.2 星星点位数据导入
- **功能描述**：用户通过JSON格式输入星星点位数据
- **数据格式**：
  ```json
  {
    "points": [
      {"id": 1, "x": 0.21, "y": 0.25},
      {"id": 2, "x": 0.2838, "y": 0.2817},
      {"id": 3, "x": 0.1, "y": 0.4428},
      {"id": 4, "x": 0.425, "y": 0.526},
      {"id": 5, "x": 0.3387, "y": 0.7812},
      {"id": 6, "x": 0.3925, "y": 0.85},
      {"id": 7, "x": 0.705, "y": 0.593},
      {"id": 8, "x": 0.6675, "y": 0.7324},
      {"id": 9, "x": 0.7838, "y": 0.6183},
      {"id": 10, "x": 0.9, "y": 0.6681}
    ],
    "connections": [[1, 2], [2, 3], [2, 4], [4, 5], [4, 6], [4, 7], [7, 8], [8, 9], [7, 9], [9, 10]]
  }
  ```
- **功能要求**：
  - 支持JSON格式验证
  - 支持相对坐标（0-1范围）和绝对坐标（像素值）
  - `points` 数组包含所有星星点的位置信息（id, x, y）
  - `connections` 数组定义星星之间的连接关系，[1,2] 表示连接 id=1 和 id=2 的点
  - 如果图片已设置，需要按比例计算实际位置

#### 1.1.3 星星绘制与连接
- **功能描述**：在画布上绘制星星，并根据连接关系用线段连接
- **实现要求**：
  - 星星按点位数据绘制在对应位置
  - 根据 connections 数组中定义的连接关系，用线段连接对应的星星
  - connections 数组中的 [id1, id2] 表示连接 id=id1 和 id=id2 的点
  - 星星和连线都支持样式自定义

#### 1.1.4 星星拖拽功能
- **功能描述**：用户可以对所有星星进行整体操作（拖拽、缩放、旋转）
- **功能要求**：
  - **组级别操作**：所有星星作为一个整体（Group）进行操作
  - **拖拽功能**：支持整体拖拽所有星星和连线
  - **缩放功能**：支持整体缩放（通过Transformer的四个角锚点）
  - **旋转功能**：支持整体旋转（通过Transformer的旋转锚点）
  - **Transform选择框**：
    - 默认不显示transform选择框，保持界面简洁
    - 点击星星或连线区域后显示transform选择框
    - 点击空白区域隐藏transform选择框
  - **连线点击区域优化**：
    - 为每条连线添加透明的宽点击层，扩大点击响应区域
    - 点击区域至少20px宽（或原始线宽的5倍），提升用户体验
    - 透明点击层不影响视觉效果，仅用于接收点击事件
  - **实时更新**：
    - 拖拽、缩放、旋转时实时更新连线位置
    - 操作结束后更新点位数据（同步到Pinia状态）
    - 重置group的transform属性，避免累积变换
  - **交互优化**：
    - 鼠标悬停在星星或连线区域时显示pointer光标
    - 移除单个星星的拖拽、悬停等交互效果
    - 所有交互统一在组级别进行

#### 1.1.5 导出功能
- **功能描述**：将当前画布内容导出为PNG或JPG图片
- **功能要求**：
  - 支持PNG和JPG两种格式
  - 支持自定义导出分辨率（2倍、3倍、4倍）
  - 导出文件名包含时间戳
  - 导出后自动下载
  - **导出时排除辅助元素**：
    - 排除Transformer（变换控制器），不导出到图片
    - 排除连线透明点击层，不导出到图片
    - 只导出可见的渲染内容（星星和连线的渲染层）
  - **背景为grid时的特殊处理**：
    - PNG格式：背景透明，不包含网格
    - JPG格式：背景为白色（#ffffff），不包含网格
    - 创建临时stage时，过滤掉Transformer和透明点击层
  - **背景为image或color时**：
    - 导出完整内容（包括背景）
    - 导出前临时隐藏Transformer和透明点击层，导出后恢复

---

## 二、功能模块详细设计

### 2.1 左侧栏 (LeftSider.vue)

#### 2.1.1 画布大小设置
- **UI设计**：使用Element-Plus的Radio组件或Tag组件
- **选项**：
  - 9:16 (竖屏比例)
  - 3:4 (标准比例)
  - 1:1 (正方形)
  - 根据图片大小自适应
- **功能要求**：
  - 选择后立即更新画布尺寸
  - 画布尺寸变化时，星星位置按比例调整
  - 自适应模式下，根据背景图片尺寸设置画布

#### 2.1.2 背景设置
- **导入本地图片**：
  - 使用Element-Plus的Upload组件
  - 支持JPG、PNG格式
  - 图片预览功能
  - 上传后自动设置为画布背景
  - 支持图片替换
  
- **设置纯色背景**：
  - 使用Element-Plus的ColorPicker组件
  - 选择颜色后立即应用
  - 清除背景图片（如果已设置）

#### 2.1.3 星星点位输入
- **UI组件**：Element-Plus的Textarea组件
- **功能要求**：
  - 输入JSON格式的星星点位数据
  - 实时验证JSON格式（错误提示）
  - "生成"按钮：解析JSON并绘制星星
  - 支持清空输入
  - 输入示例显示

---

### 2.2 右侧栏 (RightSider.vue)

#### 2.2.1 星星样式设置
- **阴影效果**：
  - 开关：启用/禁用阴影
  - 阴影颜色选择器
  - 阴影模糊度滑块（20-100，默认值：25）
  - 阴影偏移X/Y滑块（-20到20）
  
- **颜色设置**：
  - 星星填充颜色选择器
  - 星星描边颜色选择器
  - 描边宽度滑块（0-10）
  - 星星大小滑块（半径：5-50）

#### 2.2.2 连线样式设置
- **线条粗细**：
  - 滑块控制（1-10）
  
- **线条类型**：
  - 单选：实线/虚线
  - 虚线时显示虚线间隔设置
  
- **阴影效果**：
  - 开关：启用/禁用阴影
  - 阴影颜色选择器
  - 阴影模糊度滑块（20-100，默认值：25）
  - 阴影偏移X/Y滑块
  
- **线条颜色**：
  - 颜色选择器

---

### 2.3 主画布 (CanvasComponent.vue)

#### 2.3.1 画布初始化
- **默认背景**：
  - 白色底
  - 灰色网格图案（使用Konva绘制）
  - 网格大小：20x20像素
  - 网格颜色：#e0e0e0

#### 2.3.2 Konva实现
- **画布结构**：
  ```
  Stage
    ├── Layer (背景层)
    │   ├── Image (背景图片)
    │   └── Group (网格图案)
    └── Layer (内容层)
        ├── Line[] (连线渲染层：外层发光、中层发光、主体线条)
        ├── Line[] (连线透明点击层：用于接收点击事件)
        ├── Group (星星组)
        │   ├── Circle[] (星星外层发光)
        │   ├── Circle[] (星星中层发光)
        │   └── Circle[] (星星主体)
        └── Transformer (变换控制器，默认隐藏)
  ```

- **星星实现**：
  - 使用Konva.Circle绘制（三层渲染：外层发光、中层发光、主体）
  - 所有星星添加到同一个Group（starsGroup）中
  - Group设置为可拖拽（draggable: true）
  - 移除单个星星的拖拽、悬停、点击等交互效果
  - 所有交互统一在Group级别处理

- **连线实现**：
  - 使用Konva.Line绘制（三层渲染：外层发光、中层发光、主体）
  - 前三层设置 `listening: false`，不接收事件，提升性能
  - 第四层：透明宽线条（`hitLine`），专门用于接收点击事件
  - 透明点击层设置 `hitStrokeWidth`，扩大点击区域（至少20px或线宽的5倍）
  - 根据 connections 数组中定义的连接关系连接星星
  - 实时跟随星星组的位置、缩放、旋转更新

- **Transformer实现**：
  - 使用Konva.Transformer控制星星组的变换
  - 默认 `visible: false`，不显示选择框
  - 提供四个角的缩放锚点和旋转锚点
  - 点击星星组或连线区域时显示
  - 点击空白区域时隐藏
  - 监听 `dragmove`、`transform` 事件实时更新连线
  - 监听 `dragend`、`transformend` 事件同步位置到store

- **坐标变换处理**：
  - 使用 `group.getTransform()` 获取group的变换矩阵
  - 使用 `transform.point()` 将原始坐标转换为变换后的坐标
  - 操作结束后，将变换后的坐标同步到store，并重置group的transform属性

#### 2.3.3 状态管理
- **使用Pinia管理**：
  - 画布配置（尺寸、背景）
  - 星星数据（点位、样式）
  - 连线数据（样式）
  - 当前选中的星星（可选）

---

## 三、数据结构设计

### 3.1 Pinia Store结构

```javascript
// store/canvas.js
{
  // 画布配置
  canvasConfig: {
    width: 800,
    height: 1200,
    aspectRatio: '9:16', // '9:16' | '3:4' | '1:1' | 'auto'
    backgroundColor: '#ffffff'
  },
  
  // 背景配置
  backgroundConfig: {
    type: 'grid', // 'grid' | 'image' | 'color'
    imageUrl: null,
    color: '#ffffff'
  },
  
  // 星星数据
  stars: [
    {
      id: 'star_1',
      originalId: 1, // 原始 id，用于连接关系
      x: 100,
      y: 150,
      radius: 10,
      fill: '#FFD700',
      stroke: '#FFA500',
      strokeWidth: 2,
      shadowEnabled: true,
      shadowColor: '#000000',
      shadowBlur: 25,
      shadowOffsetX: 2,
      shadowOffsetY: 2
    }
  ],
  
  // 连接关系数据
  connections: [[1, 2], [2, 3]], // [id1, id2] 表示连接关系

  // 连线数据
  lines: [
    {
      id: 'line_1',
      fromStarId: 'star_1',
      toStarId: 'star_2',
      points: [100, 150, 200, 180],
      stroke: '#000000',
      strokeWidth: 2,
      dash: [],
      shadowEnabled: false,
      shadowColor: '#000000',
      shadowBlur: 25,
      shadowOffsetX: 1,
      shadowOffsetY: 1
    }
  ],
  
  // 星星样式（全局默认）
  starStyle: {
    radius: 10,
    fill: '#FFD700',
    stroke: '#FFA500',
    strokeWidth: 2,
    shadowEnabled: true,
    shadowColor: '#000000',
    shadowBlur: 5,
    shadowOffsetX: 2,
    shadowOffsetY: 2
  },
  
  // 连线样式（全局默认）
  lineStyle: {
    stroke: '#000000',
    strokeWidth: 2,
    dash: [],
    shadowEnabled: false,
    shadowColor: '#000000',
    shadowBlur: 25,
    shadowOffsetX: 1,
    shadowOffsetY: 1
  },
  
  // 当前选中星星
  selectedStarId: null
}
```

### 3.2 默认样式配置文件 (defaultStyles.json)

`defaultStyles.json` 文件用于存储星星和连线的默认样式配置，便于统一管理和修改默认样式。

#### 文件位置
`src/stores/defaultStyles.json`

#### 数据结构

```json
{
  "star": {
    "radius": 3,
    "fill": "#00FFFF",
    "stroke": "#00FFFF",
    "strokeWidth": 0,
    "shadowEnabled": true,
    "shadowColor": "#00FFFF",
    "shadowBlur": 50,
    "shadowOffsetX": 0,
    "shadowOffsetY": 0,
    "opacity": 1
  },
  "line": {
    "stroke": "#00FFFF",
    "strokeWidth": 1,
    "dash": [],
    "shadowEnabled": true,
    "shadowColor": "#00FFFF",
    "shadowBlur": 50,
    "shadowOffsetX": 0,
    "shadowOffsetY": 0,
    "opacity": 0.95
  }
}
```

#### 字段说明

**星星样式 (star)**：
- `radius`: 星星半径（像素），默认值：3
- `fill`: 填充颜色，默认值："#00FFFF"（青色）
- `stroke`: 描边颜色，默认值："#00FFFF"（青色）
- `strokeWidth`: 描边宽度（像素），默认值：0
- `shadowEnabled`: 是否启用阴影，默认值：true
- `shadowColor`: 阴影颜色，默认值："#00FFFF"（青色）
- `shadowBlur`: 阴影模糊度，范围：20-100，默认值：25（产生光晕效果）
- `shadowOffsetX`: 阴影X轴偏移（像素），默认值：0
- `shadowOffsetY`: 阴影Y轴偏移（像素），默认值：0
- `opacity`: 透明度（0-1），默认值：1

**连线样式 (line)**：
- `stroke`: 线条颜色，默认值："#00FFFF"（青色）
- `strokeWidth`: 线条宽度（像素），默认值：1
- `dash`: 虚线样式数组，默认值：[]（实线）
- `shadowEnabled`: 是否启用阴影，默认值：true
- `shadowColor`: 阴影颜色，默认值："#00FFFF"（青色）
- `shadowBlur`: 阴影模糊度，范围：20-100，默认值：25
- `shadowOffsetX`: 阴影X轴偏移（像素），默认值：0
- `shadowOffsetY`: 阴影Y轴偏移（像素），默认值：0
- `opacity`: 透明度（0-1），默认值：0.95

#### 使用方式

1. **初始化**：Pinia store (`canvas.js`) 在初始化时从该文件读取默认样式
2. **重置样式**：右侧栏的"重置样式"按钮会从该文件重新加载默认样式
3. **修改默认值**：直接编辑该JSON文件即可修改全局默认样式

### 3.3 星星点位JSON格式

数据格式为包含 `points` 和 `connections` 的对象：

#### 格式1：相对坐标（0-1范围）
```json
{
  "points": [
    {"id": 1, "x": 0.1, "y": 0.15},
    {"id": 2, "x": 0.2, "y": 0.18},
    {"id": 3, "x": 0.3, "y": 0.12}
  ],
  "connections": [[1, 2], [2, 3]]
}
```

#### 格式2：绝对坐标（像素）
```json
{
  "points": [
    {"id": 1, "x": 100, "y": 150},
    {"id": 2, "x": 200, "y": 180},
    {"id": 3, "x": 300, "y": 120}
  ],
  "connections": [[1, 2], [2, 3]]
}
```

#### 格式3：带样式信息（可选）
```json
{
  "points": [
    {
      "id": 1,
      "x": 100,
      "y": 150,
      "radius": 12,
      "fill": "#FFD700"
    }
  ],
  "connections": []
}
```

---

## 四、交互流程设计

### 4.1 初始化流程
1. 页面加载 → 显示默认网格背景
2. 画布尺寸：默认9:16比例
3. 等待用户操作

### 4.2 设置背景流程
1. 用户选择背景类型（图片/纯色）
2. 如果选择图片：
   - 点击上传按钮
   - 选择本地图片文件
   - 图片加载后设置为背景
   - 如果选择"自适应"，画布尺寸调整为图片尺寸
3. 如果选择纯色：
   - 打开颜色选择器
   - 选择颜色后应用
   - 清除背景图片（如果存在）

### 4.3 导入星星点位流程
1. 用户在左侧栏Textarea输入JSON数据
2. 点击"生成"按钮
3. 验证JSON格式：
   - 格式错误 → 显示错误提示
   - 格式正确 → 继续处理
4. 解析JSON数据：
   - 判断坐标类型（绝对/相对）
   - 如果是相对坐标且有背景图片，转换为绝对坐标
5. 创建星星对象：
   - 生成唯一ID
   - 应用当前星星样式
   - 添加到Pinia store
6. 生成连线：
   - 根据 connections 数组中的连接关系生成连线
   - 应用当前连线样式
7. 更新画布显示

### 4.4 星星组操作流程
1. **显示Transform选择框**：
   - 用户点击星星或连线区域
   - 显示Transformer选择框（四个角锚点和旋转锚点）

2. **拖拽操作**：
   - 用户拖拽星星组
   - 拖拽过程中：
     - 所有星星和连线跟随鼠标移动
     - 连线位置实时更新
   - 拖拽结束：
     - 计算变换后的星星位置
     - 更新所有星星位置到Pinia store
     - 重置group的transform属性
     - 重新渲染画布

3. **缩放操作**：
   - 用户拖拽Transformer的四个角锚点
   - 缩放过程中：
     - 所有星星和连线按比例缩放
     - 连线位置实时更新
   - 缩放结束：
     - 计算变换后的星星位置和大小
     - 更新所有星星数据到Pinia store
     - 重置group的transform属性
     - 重新渲染画布

4. **旋转操作**：
   - 用户拖拽Transformer的旋转锚点
   - 旋转过程中：
     - 所有星星和连线围绕中心点旋转
     - 连线位置实时更新
   - 旋转结束：
     - 计算变换后的星星位置
     - 更新所有星星位置到Pinia store
     - 重置group的transform属性
     - 重新渲染画布

5. **隐藏Transform选择框**：
   - 用户点击空白区域（背景）
   - 隐藏Transformer选择框

### 4.5 修改样式流程
1. 用户在右侧栏修改样式参数
2. 实时更新Pinia store中的样式配置
3. 应用样式到所有星星/连线：
   - 如果选中单个星星，只更新该星星
   - 如果未选中，更新全局默认样式
4. 重新渲染画布

### 4.6 导出流程
1. 用户点击导出按钮（可在Header或右侧栏）
2. 弹出导出对话框，用户选择导出分辨率和格式
3. 用户点击"确认导出"
4. 根据背景类型和导出格式处理：
   - **背景为grid时**：
     - PNG格式：创建临时stage，不包含网格背景，背景透明
     - JPG格式：创建临时stage，不包含网格背景，添加白色背景（#ffffff）
     - 复制内容层节点时，过滤掉Transformer和透明点击层（`name === 'clickableLine'）
   - **背景为image或color时**：
     - 临时隐藏Transformer和透明点击层
     - 导出原stage（包含背景）
     - 导出后恢复Transformer和透明点击层的可见性
5. 转换为图片：
   - 使用Konva的toDataURL方法
   - 设置导出质量（可选）
   - 支持2倍、3倍、4倍分辨率
6. 创建下载链接
7. 触发下载
8. 文件名格式：`star-pattern-YYYYMMDD-HHmmss.png` 或 `star-pattern-YYYYMMDD-HHmmss.jpg`

---

## 五、技术实现要点

### 5.1 Konva画布管理
- **图层分离**：背景层和内容层分开，便于管理
- **组级别操作**：所有星星添加到同一个Group，统一进行拖拽、缩放、旋转操作
- **事件处理**：
  - 星星组拖拽事件（`dragmove`、`dragend`）
  - Transformer变换事件（`transform`、`transformend`）
  - 画布点击事件（显示/隐藏Transformer）
  - 连线透明点击层点击事件
- **性能优化**：
  - 使用Layer.batchDraw()批量更新
  - 连线渲染层设置 `listening: false`，不接收事件
  - 只有透明点击层接收事件，减少事件处理开销

### 5.2 坐标转换
- **相对坐标转绝对坐标**：
  ```javascript
  absoluteX = relativeX * canvasWidth
  absoluteY = relativeY * canvasHeight
  ```
- **图片坐标转画布坐标**：
  - 如果图片尺寸与画布不一致，需要按比例缩放
- **组变换坐标转换**：
  ```javascript
  // 获取group的变换矩阵
  const groupTransform = starsGroup.getTransform()

  // 将原始坐标转换为变换后的坐标
  const transformedPoint = groupTransform.point({ x: originalX, y: originalY })

  // 更新连线位置
  line.points([transformedPoint.x, transformedPoint.y, ...])

  // 操作结束后，同步到store并重置transform
  starsGroup.position({ x: 0, y: 0 })
  starsGroup.rotation(0)
  starsGroup.scale({ x: 1, y: 1 })
  ```

### 5.3 网格背景实现
- 使用Konva.Line绘制网格线
- 计算网格数量：`Math.ceil(width / gridSize)`
- 批量绘制提高性能

### 5.4 图片加载处理
- 使用Image对象预加载
- 监听onload事件
- 加载完成后创建Konva.Image

### 5.5 导出功能实现

#### 5.5.1 基础导出
```javascript
// 导出为JPG
const dataURL = stage.toDataURL({
  mimeType: 'image/jpeg',
  quality: 0.95,
  pixelRatio: 2 // 提高导出分辨率
})

// 导出为PNG
const dataURL = stage.toDataURL({
  mimeType: 'image/png',
  pixelRatio: 2
})
```

#### 5.5.2 Grid背景特殊处理
当背景类型为"grid"时，导出时需要特殊处理：

- **PNG格式**：
  - 创建临时stage，只包含内容层（星星和连线）
  - 不包含网格背景，背景保持透明
  - 复制内容层节点时，过滤掉Transformer和透明点击层（`name === 'clickableLine'`）
  - 适用于需要透明背景的场景

- **JPG格式**：
  - 创建临时stage，只包含内容层（星星和连线）
  - 添加白色背景矩形（#ffffff）
  - 不包含网格背景
  - 复制内容层节点时，过滤掉Transformer和透明点击层
  - JPG不支持透明，因此使用白色背景

#### 5.5.3 非Grid背景导出处理
当背景类型为"image"或"color"时：

- **导出前处理**：
  - 保存Transformer和透明点击层的可见性状态
  - 临时隐藏Transformer和透明点击层
  - 调用 `contentLayer.batchDraw()` 更新画布

- **导出操作**：
  - 直接使用原stage的 `toDataURL()` 方法导出
  - 包含背景图片或背景颜色

- **导出后处理**：
  - 恢复Transformer和透明点击层的可见性
  - 调用 `contentLayer.batchDraw()` 更新画布

---

## 六、UI/UX设计要求

### 6.1 布局要求
- 左侧栏宽度：350px（固定）
- 右侧栏宽度：250px（固定）
- 主画布：自适应剩余空间
- 响应式：小屏幕时可折叠侧边栏

### 6.2 交互反馈
- 按钮hover效果
- 星星组操作反馈：
  - 鼠标悬停在星星或连线区域时显示pointer光标
  - 点击星星或连线区域后显示Transformer选择框
  - 拖拽、缩放、旋转时实时更新连线位置
- 输入验证实时提示
- 操作成功/失败提示（使用Element-Plus Message）

### 6.3 视觉设计
- 使用Element-Plus组件保持一致性
- TailwindCSS实现样式
- 颜色搭配：主色调 + 辅助色
- 图标使用Element-Plus Icons

---

## 七、边界情况处理

### 7.1 数据验证
- JSON格式验证
- 坐标范围验证（不能超出画布）
- 图片格式验证（只支持JPG、PNG）
- 图片大小限制（建议最大5MB）

### 7.2 错误处理
- 图片加载失败提示
- JSON解析错误提示
- 导出失败提示
- 网络错误处理（如果后续有网络功能）

### 7.3 性能优化
- 大量星星时使用虚拟渲染（可选）
- 拖拽时使用节流优化
- 图片压缩处理（如果过大）

---

## 八、后续扩展功能（可选）

1. **撤销/重做功能**：记录操作历史
2. **多组星星管理**：支持多个独立的星星组
3. **模板保存/加载**：保存当前配置
4. **快捷键支持**：提高操作效率
5. **星星分组**：不同组使用不同样式
6. **导入/导出配置**：保存整个项目配置

---

## 九、开发优先级

### Phase 1: 核心功能
1. 画布基础设置（尺寸、背景）
2. 星星点位导入和绘制
3. 星星连接功能
4. 基础拖拽功能

### Phase 2: 样式定制
1. 星星样式设置
2. 连线样式设置
3. 样式实时预览

### Phase 3: 高级功能
1. 导出功能
2. 交互优化
3. 错误处理完善

---

## 十、测试要点

1. **功能测试**：
   - 背景图片上传和显示
   - JSON数据导入和解析
   - 星星绘制和连接
   - 拖拽功能
   - 样式修改
   - 导出功能

2. **边界测试**：
   - 空数据导入
   - 错误JSON格式
   - 超大图片
   - 大量星星（性能测试）

3. **兼容性测试**：
   - 不同浏览器
   - 不同屏幕尺寸

---

## 十一、备注

- 所有坐标系统以画布左上角为原点(0,0)
- 星星id从1开始递增
- 连线按id顺序连接，不形成闭环（除非最后一个连接回第一个）
- 导出图片分辨率建议为画布的2倍（retina显示）
