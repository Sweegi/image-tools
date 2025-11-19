<template>
  <div class="canvas-container">
    <div class="canvas-wrapper" ref="canvasWrapper">
      <div ref="canvasContainer" class="konva-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import Konva from 'konva'
import { useCanvasStore } from '@/stores/canvas'
import { ElMessage } from 'element-plus'

const canvasStore = useCanvasStore()

// 模板引用
const canvasWrapper = ref(null)
const canvasContainer = ref(null)

// Konva 对象
let stage = null
let backgroundLayer = null
let contentLayer = null
let gridGroup = null
let backgroundImage = null
let backgroundColorRect = null
let starsGroup = null
let transformer = null

// 响应式数据
const stageConfig = ref({ // 默认 9：16
  width: 400,
  height: Math.round(400 * 16 / 9)
})

// 初始化画布
const initCanvas = () => {
  if (!canvasContainer.value) return

  // 创建舞台
  stage = new Konva.Stage({
    container: canvasContainer.value,
    width: stageConfig.value.width,
    height: stageConfig.value.height
  })

  // 创建背景层
  backgroundLayer = new Konva.Layer()
  stage.add(backgroundLayer)

  // 创建内容层
  contentLayer = new Konva.Layer()
  stage.add(contentLayer)

  // 初始化网格背景
  createGridBackground()

  // 绑定导出事件
  window.addEventListener('export-canvas', handleExportCanvas)
}

// 创建网格背景
const createGridBackground = () => {
  if (gridGroup) {
    gridGroup.destroy()
    gridGroup = null
  }

  // 清除背景图片
  if (backgroundImage) {
    backgroundImage.destroy()
    backgroundImage = null
  }

  // 清除背景色矩形
  if (backgroundColorRect) {
    backgroundColorRect.destroy()
    backgroundColorRect = null
  }

  gridGroup = new Konva.Group()
  
  const gridSize = 20
  const { width, height } = stageConfig.value

  // 绘制垂直线
  for (let i = 0; i <= width; i += gridSize) {
    const line = new Konva.Line({
      points: [i, 0, i, height],
      stroke: '#e0e0e0',
      strokeWidth: 1
    })
    gridGroup.add(line)
  }

  // 绘制水平线
  for (let i = 0; i <= height; i += gridSize) {
    const line = new Konva.Line({
      points: [0, i, width, i],
      stroke: '#e0e0e0',
      strokeWidth: 1
    })
    gridGroup.add(line)
  }

  backgroundLayer.add(gridGroup)
  backgroundLayer.batchDraw()
}

// 设置背景图片
const setBackgroundImage = (imageUrl) => {
  if (backgroundImage) {
    backgroundImage.destroy()
    backgroundImage = null
  }

  // 清除背景色矩形
  if (backgroundColorRect) {
    backgroundColorRect.destroy()
    backgroundColorRect = null
  }

  // 清除网格
  if (gridGroup) {
    gridGroup.destroy()
    gridGroup = null
  }

  if (!imageUrl) {
    backgroundLayer.batchDraw()
    return
  }

  const img = new Image()
  img.onload = () => {
    backgroundImage = new Konva.Image({
      x: 0,
      y: 0,
      image: img,
      width: stageConfig.value.width,
      height: stageConfig.value.height
    })
    
    // 将背景图片添加到背景层
    backgroundLayer.add(backgroundImage)
    backgroundImage.moveToTop()
    backgroundLayer.batchDraw()
  }
  img.src = imageUrl
}

// 设置背景颜色
const setBackgroundColor = (color) => {
  // 先清除背景图片
  if (backgroundImage) {
    backgroundImage.destroy()
    backgroundImage = null
  }

  // 清除旧的网格
  if (gridGroup) {
    gridGroup.destroy()
    gridGroup = null
  }

  // 清除旧的背景色矩形
  if (backgroundColorRect) {
    backgroundColorRect.destroy()
    backgroundColorRect = null
  }

  // 创建背景色矩形作为背景层的最底层
  if (stage && backgroundLayer) {
    backgroundColorRect = new Konva.Rect({
      x: 0,
      y: 0,
      width: stageConfig.value.width,
      height: stageConfig.value.height,
      fill: color
    })
    backgroundLayer.add(backgroundColorRect)
    backgroundColorRect.moveToBottom()
    backgroundLayer.batchDraw()
  }
}

// 渲染星星
const renderStars = () => {
  // 清除现有的星星和连线
  contentLayer.destroyChildren()

  // 清除旧的transformer
  if (transformer) {
    transformer.destroy()
    transformer = null
  }

  const stars = canvasStore.stars
  const lines = canvasStore.lines

  // 渲染连线（双层渲染技术）
  lines.forEach(line => {
    // 第一层：外层发光（最大范围、最模糊）
    const outerGlowLine = new Konva.Line({
      points: line.points,
      stroke: line.shadowColor || line.stroke,
      strokeWidth: line.strokeWidth * 3,
      dash: line.dash,
      opacity: 0.15,
      shadowEnabled: true,
      shadowColor: line.shadowColor || line.stroke,
      shadowBlur: (line.shadowBlur || 20) * 2.5,
      shadowOffsetX: 0,
      shadowOffsetY: 0,
      listening: false
    })
    contentLayer.add(outerGlowLine)

    // 第二层：中层发光（中等范围）
    const middleGlowLine = new Konva.Line({
      points: line.points,
      stroke: line.shadowColor || line.stroke,
      strokeWidth: line.strokeWidth * 1.8,
      dash: line.dash,
      opacity: 0.3,
      shadowEnabled: true,
      shadowColor: line.shadowColor || line.stroke,
      shadowBlur: (line.shadowBlur || 20) * 1.5,
      shadowOffsetX: 0,
      shadowOffsetY: 0,
      listening: false
    })
    contentLayer.add(middleGlowLine)

    // 第三层：主体线条
    const konvaLine = new Konva.Line({
      points: line.points,
      stroke: line.stroke,
      strokeWidth: line.strokeWidth,
      dash: line.dash,
      shadowEnabled: line.shadowEnabled,
      shadowColor: line.shadowColor,
      shadowBlur: line.shadowBlur,
      shadowOffsetX: line.shadowOffsetX,
      shadowOffsetY: line.shadowOffsetY,
      opacity: line.opacity !== undefined ? line.opacity : 1,
      listening: false
    })
    contentLayer.add(konvaLine)

    // 第四层：透明的宽线条用于接收点击事件（扩大点击区域）
    const hitLine = new Konva.Line({
      points: line.points,
      stroke: 'transparent',
      strokeWidth: Math.max(20, line.strokeWidth * 5),
      hitStrokeWidth: Math.max(20, line.strokeWidth * 5),
      listening: true,
      name: 'clickableLine'
    })

    // 给透明线条添加点击事件
    hitLine.on('click tap', (e) => {
      e.cancelBubble = true
      transformer.visible(true)
      transformer.nodes([starsGroup])
      contentLayer.batchDraw()
    })

    // 添加悬停效果
    hitLine.on('mouseenter', () => {
      document.body.style.cursor = 'pointer'
    })

    hitLine.on('mouseleave', () => {
      document.body.style.cursor = 'default'
    })

    contentLayer.add(hitLine)
  })

  // 创建星星组
  starsGroup = new Konva.Group({
    name: 'starsGroup',
    draggable: true
  })

  // 渲染星星（双层渲染技术）
  stars.forEach(star => {
    const baseRadius = Math.max(2, star.radius)

    // 第一层：外层发光（最大范围、最模糊）
    const outerGlow = new Konva.Circle({
      x: star.x,
      y: star.y,
      radius: baseRadius * 2.5,
      fill: star.shadowColor || star.fill,
      opacity: 0.1,
      shadowEnabled: true,
      shadowColor: star.shadowColor || star.fill,
      shadowBlur: (star.shadowBlur || 25) * 2.5,
      shadowOffsetX: 0,
      shadowOffsetY: 0
    })
    starsGroup.add(outerGlow)

    // 第二层：中层发光（中等范围）
    const middleGlow = new Konva.Circle({
      x: star.x,
      y: star.y,
      radius: baseRadius * 1.5,
      fill: star.shadowColor || star.fill,
      opacity: 0.25,
      shadowEnabled: true,
      shadowColor: star.shadowColor || star.fill,
      shadowBlur: (star.shadowBlur || 25) * 1.5,
      shadowOffsetX: 0,
      shadowOffsetY: 0
    })
    starsGroup.add(middleGlow)

    // 第三层：主体星星
    const circle = new Konva.Circle({
      x: star.x,
      y: star.y,
      radius: baseRadius,
      fill: star.fill,
      stroke: star.stroke,
      strokeWidth: star.strokeWidth,
      shadowEnabled: star.shadowEnabled,
      shadowColor: star.shadowColor,
      shadowBlur: star.shadowBlur,
      shadowOffsetX: star.shadowOffsetX,
      shadowOffsetY: star.shadowOffsetY,
      opacity: star.opacity !== undefined ? star.opacity : 1,
      id: star.id
    })

    starsGroup.add(circle)
  })

  contentLayer.add(starsGroup)

  // 创建Transformer
  transformer = new Konva.Transformer({
    nodes: [starsGroup],
    visible: false,
    enabledAnchors: ['top-left', 'top-right', 'bottom-left', 'bottom-right'],
    rotateEnabled: true,
    borderStroke: '#4A90E2',
    borderStrokeWidth: 2,
    anchorStroke: '#4A90E2',
    anchorFill: '#fff',
    anchorSize: 8,
    keepRatio: false
  })

  contentLayer.add(transformer)

  // 点击星星组显示transformer
  starsGroup.on('click tap', (e) => {
    e.cancelBubble = true
    transformer.visible(true)
    transformer.nodes([starsGroup])
    contentLayer.batchDraw()
  })

  // 星星组悬停效果
  starsGroup.on('mouseenter', () => {
    document.body.style.cursor = 'pointer'
  })

  starsGroup.on('mouseleave', () => {
    document.body.style.cursor = 'default'
  })

  // 点击空白区域隐藏transformer
  stage.on('click tap', (e) => {
    // 如果点击的是transformer，不处理
    if (e.target === transformer || e.target.getParent() === transformer) {
      return
    }

    // 如果点击的是starsGroup，不处理（已经在上面处理了）
    if (e.target.getParent() === starsGroup || e.target === starsGroup) {
      return
    }

    // 如果点击的是连线（透明点击层），不处理
    if (e.target.name() === 'clickableLine') {
      return
    }

    // 点击其他区域隐藏transformer
    transformer.visible(false)
    contentLayer.batchDraw()
  })

  // 监听group的transform变化，更新连线
  starsGroup.on('dragmove transform', () => {
    updateLinesFromGroup()
    contentLayer.batchDraw()
  })

  // transform结束后更新store中的星星位置
  starsGroup.on('dragend transformend', () => {
    updateStarPositionsToStore()
  })

  contentLayer.batchDraw()
}

// 更新连线
const updateLines = () => {
  const lines = canvasStore.lines
  const lineNodes = contentLayer.find('Line')
  
  lines.forEach((line, index) => {
    if (lineNodes[index]) {
      lineNodes[index].points(line.points)
    }
  })
  
  contentLayer.batchDraw()
}

// 根据group的transform更新连线位置
const updateLinesFromGroup = () => {
  if (!starsGroup) return

  const stars = canvasStore.stars
  const lines = canvasStore.lines
  const lineNodes = contentLayer.find('Line')

  // 获取group的transform属性
  const groupTransform = starsGroup.getTransform()

  // 更新连线点位
  lines.forEach((line, lineIndex) => {
    const newPoints = []

    // 每条线由起点和终点组成，points数组是[x1, y1, x2, y2]格式
    for (let i = 0; i < line.points.length; i += 2) {
      const x = line.points[i]
      const y = line.points[i + 1]

      // 应用group的transform到原始点
      const transformedPoint = groupTransform.point({ x, y })
      newPoints.push(transformedPoint.x, transformedPoint.y)
    }

    // 更新对应的线条（每条线有4个konva对象：外层、中层、主体、透明点击层）
    const startIndex = lineIndex * 4
    if (lineNodes[startIndex]) {
      lineNodes[startIndex].points(newPoints)
    }
    if (lineNodes[startIndex + 1]) {
      lineNodes[startIndex + 1].points(newPoints)
    }
    if (lineNodes[startIndex + 2]) {
      lineNodes[startIndex + 2].points(newPoints)
    }
    if (lineNodes[startIndex + 3]) {
      lineNodes[startIndex + 3].points(newPoints)
    }
  })
}

// transform结束后更新store中的星星位置
const updateStarPositionsToStore = () => {
  if (!starsGroup) return

  const stars = canvasStore.stars
  const groupTransform = starsGroup.getTransform()

  // 更新每个星星的位置到store
  stars.forEach(star => {
    const transformedPoint = groupTransform.point({ x: star.x, y: star.y })
    canvasStore.updateStarPosition(star.id, transformedPoint.x, transformedPoint.y)
  })

  // 重置group的transform，因为位置已经更新到store
  starsGroup.position({ x: 0, y: 0 })
  starsGroup.rotation(0)
  starsGroup.scale({ x: 1, y: 1 })

  // 重新渲染以应用新的位置
  renderStars()
}

// 更新画布尺寸
const updateCanvasSize = () => {
  const dimensions = canvasStore.canvasDimensions
  stageConfig.value = {
    width: dimensions.width,
    height: dimensions.height
  }

  if (stage) {
    stage.width(dimensions.width)
    stage.height(dimensions.height)
    
    // 根据背景类型重新设置背景
    const bgConfig = canvasStore.backgroundConfig
    
    switch (bgConfig.type) {
      case 'grid':
        createGridBackground()
        break
      case 'image':
        if (bgConfig.imageUrl) {
          setBackgroundImage(bgConfig.imageUrl)
        }
        break
      case 'color':
        if (bgConfig.color) {
          // 如果背景色矩形已存在，只需更新尺寸，否则重新创建
          if (backgroundColorRect) {
            backgroundColorRect.width(dimensions.width)
            backgroundColorRect.height(dimensions.height)
            backgroundLayer.batchDraw()
          } else {
            setBackgroundColor(bgConfig.color)
          }
        }
        break
    }
    
    // 重新渲染星星
    renderStars()
  }
}

// 处理背景变化
const handleBackgroundChange = () => {
  const bgConfig = canvasStore.backgroundConfig
  
  switch (bgConfig.type) {
    case 'grid':
      if (backgroundImage) {
        backgroundImage.destroy()
        backgroundImage = null
      }
      // 清除背景色矩形
      if (backgroundColorRect) {
        backgroundColorRect.destroy()
        backgroundColorRect = null
      }
      createGridBackground()
      break
    case 'image':
      if (bgConfig.imageUrl) {
        setBackgroundImage(bgConfig.imageUrl)
      }
      break
    case 'color':
      setBackgroundColor(bgConfig.color)
      break
  }
}

// 导出画布
const handleExportCanvas = (event) => {
  if (!stage) {
    ElMessage.error('画布未初始化')
    return
  }

  try {
    // 从事件中获取导出选项，如果没有则使用默认值
    const options = event?.detail || {}
    const {
      pixelRatio = 3, // 默认 3 倍分辨率，可根据需要调整（2-4 倍）
      mimeType = 'image/png', // 默认 PNG 格式（无损），可选 'image/jpeg'
      quality = 0.95 // JPG 质量（仅对 JPG 有效）
    } = options

    const bgConfig = canvasStore.backgroundConfig
    const isGridBackground = bgConfig.type === 'grid'
    const isPNG = mimeType === 'image/png'
    const isJPG = mimeType === 'image/jpeg'

    // 当背景为grid时，需要特殊处理
    if (isGridBackground) {
      // 创建隐藏的临时container用于导出
      const tempContainer = document.createElement('div')
      tempContainer.style.position = 'absolute'
      tempContainer.style.left = '-9999px'
      tempContainer.style.top = '-9999px'
      tempContainer.style.width = `${stage.width()}px`
      tempContainer.style.height = `${stage.height()}px`
      document.body.appendChild(tempContainer)

      let tempStage = null
      try {
        // 创建临时stage用于导出
        tempStage = new Konva.Stage({
          container: tempContainer,
          width: stage.width(),
          height: stage.height()
        })

        // 创建临时背景层
        const tempBackgroundLayer = new Konva.Layer()
        tempStage.add(tempBackgroundLayer)

        // 如果是JPG格式，添加白色背景
        if (isJPG) {
          const whiteRect = new Konva.Rect({
            x: 0,
            y: 0,
            width: stage.width(),
            height: stage.height(),
            fill: '#ffffff'
          })
          tempBackgroundLayer.add(whiteRect)
        }
        // PNG格式不添加背景，保持透明

        // 创建临时内容层，复制所有内容
        const tempContentLayer = new Konva.Layer()
        tempStage.add(tempContentLayer)

        // 复制内容层的所有节点，但排除transformer和透明点击层
        contentLayer.children.forEach(node => {
          // 跳过 Transformer 和透明点击层
          if (node === transformer || node.name() === 'clickableLine') {
            return
          }
          const clonedNode = node.clone()
          tempContentLayer.add(clonedNode)
        })

        tempBackgroundLayer.draw()
        tempContentLayer.draw()

        // 导出临时stage
        const dataURL = tempStage.toDataURL({
          mimeType,
          quality,
          pixelRatio
        })

        // 创建下载链接
        const link = document.createElement('a')
        const extension = isPNG ? 'png' : 'jpg'
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
        link.download = `star-pattern-${timestamp}.${extension}`
        link.href = dataURL
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        const ratioText = pixelRatio === 2 ? '标准高清' : pixelRatio === 3 ? '超高清' : '极致高清'
        ElMessage.success(`${ratioText}图片导出成功`)
      } finally {
        // 无论成功或失败，都清理临时资源
        if (tempStage) {
          tempStage.destroy()
        }
        if (tempContainer && tempContainer.parentNode) {
          document.body.removeChild(tempContainer)
        }
      }
    } else {
      // 非grid背景，直接导出原stage
      // 临时隐藏transformer和透明点击层
      const transformerVisible = transformer ? transformer.visible() : false
      const clickableLines = contentLayer.find('.clickableLine')

      if (transformer) {
        transformer.visible(false)
      }
      clickableLines.forEach(line => {
        line.visible(false)
      })

      contentLayer.batchDraw()

      const dataURL = stage.toDataURL({
        mimeType,
        quality,
        pixelRatio
      })

      // 恢复transformer和透明点击层的可见性
      if (transformer) {
        transformer.visible(transformerVisible)
      }
      clickableLines.forEach(line => {
        line.visible(true)
      })

      contentLayer.batchDraw()

      // 创建下载链接
      const link = document.createElement('a')
      const extension = isPNG ? 'png' : 'jpg'
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
      link.download = `star-pattern-${timestamp}.${extension}`
      link.href = dataURL
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      const ratioText = pixelRatio === 2 ? '标准高清' : pixelRatio === 3 ? '超高清' : '极致高清'
      ElMessage.success(`${ratioText}图片导出成功`)
    }
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export error:', error)
  }
}

// 监听store变化
watch(() => canvasStore.stars, renderStars, { deep: true })
watch(() => canvasStore.lines, renderStars, { deep: true })
watch(() => canvasStore.canvasDimensions, updateCanvasSize, { deep: true })
watch(() => canvasStore.backgroundConfig, handleBackgroundChange, { deep: true })

// 生命周期
onMounted(() => {
  nextTick(() => {
    initCanvas()
  })
})

onUnmounted(() => {
  if (stage) {
    stage.destroy()
  }
  window.removeEventListener('export-canvas', handleExportCanvas)
})
</script>

<style scoped>
.canvas-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  padding: 20px;
}

.canvas-wrapper {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 10px;
  max-width: 100%;
  max-height: 100%;
  overflow: auto;
}

.konva-container {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

:deep(canvas) {
  display: block;
}
</style>
