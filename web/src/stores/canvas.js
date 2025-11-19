import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import defaultStyles from './defaultStyles.json'

export const useCanvasStore = defineStore('canvas', () => {
  // 画布配置
  const canvasConfig = ref({
    width: 800,
    height: 1200,
    aspectRatio: '9:16', // '9:16' | '3:4' | '1:1' | 'auto'
    backgroundColor: '#ffffff'
  })

  // 背景配置
  const backgroundConfig = ref({
    type: 'grid', // 'grid' | 'image' | 'color'
    imageUrl: null,
    color: '#ffffff'
  })

  // 星星数据
  const stars = ref([])

  // 连线数据
  const lines = ref([])

  // 连接关系数据
  const connections = ref([])

  // 星星样式（全局默认）- 从JSON配置文件读取
  const starStyle = ref({
    ...defaultStyles.star
  })

  // 连线样式（全局默认）- 从JSON配置文件读取
  const lineStyle = ref({
    ...defaultStyles.line
  })

  // 当前选中星星
  const selectedStarId = ref(null)

  // 计算属性：根据宽高比计算画布尺寸
  const canvasDimensions = computed(() => {
    const { aspectRatio } = canvasConfig.value
    let width = 400
    let height = Math.round(width * 16 / 9)

    switch (aspectRatio) {
      case '9:16':
        height = Math.round(width * 16 / 9)
        break
      case '3:4':
        height = Math.round(width * 4 / 3)
        break
      case '1:1':
        height = width
        break
      case 'auto':
        // 如果有背景图片，使用图片尺寸
        width = canvasConfig.value.width
        height = canvasConfig.value.height
        break
    }

    return { width, height }
  })

  // Actions
  const updateCanvasConfig = (config) => {
    canvasConfig.value = { ...canvasConfig.value, ...config }
  }

  const updateBackgroundConfig = (config) => {
    backgroundConfig.value = { ...backgroundConfig.value, ...config }
  }

  const setStars = (newStars, newConnections = []) => {
    // 创建 id 到 star 对象的映射
    const idToStarMap = {}
    newStars.forEach(star => {
      idToStarMap[star.id] = star
    })

    // 根据 points 数据创建星星对象
    stars.value = newStars.map(star => ({
      id: `star_${star.id}`,
      originalId: star.id, // 保存原始 id，用于连接关系
      x: star.x,
      y: star.y,
      radius: Math.max(2, star.radius !== undefined ? star.radius : starStyle.value.radius),
      fill: star.fill || starStyle.value.fill,
      stroke: star.stroke !== undefined ? star.stroke : starStyle.value.stroke,
      strokeWidth: star.strokeWidth !== undefined ? star.strokeWidth : starStyle.value.strokeWidth,
      shadowEnabled: star.shadowEnabled !== undefined ? star.shadowEnabled : starStyle.value.shadowEnabled,
      shadowColor: star.shadowColor || starStyle.value.shadowColor,
      shadowBlur: star.shadowBlur !== undefined ? star.shadowBlur : starStyle.value.shadowBlur,
      shadowOffsetX: star.shadowOffsetX !== undefined ? star.shadowOffsetX : starStyle.value.shadowOffsetX,
      shadowOffsetY: star.shadowOffsetY !== undefined ? star.shadowOffsetY : starStyle.value.shadowOffsetY,
      opacity: star.opacity !== undefined ? star.opacity : starStyle.value.opacity
    }))

    // 保存连接关系
    connections.value = newConnections

    // 根据连接关系生成连线
    generateLines()
  }

  const updateStarPosition = (starId, x, y) => {
    const star = stars.value.find(s => s.id === starId)
    if (star) {
      star.x = x
      star.y = y
      generateLines()
    }
  }

  const generateLines = () => {
    lines.value = []

    // 创建 originalId 到 star 对象的映射
    const idToStarMap = {}
    stars.value.forEach(star => {
      idToStarMap[star.originalId] = star
    })

    // 根据 connections 数组生成连线
    connections.value.forEach((conn, index) => {
      const [fromId, toId] = conn
      const fromStar = idToStarMap[fromId]
      const toStar = idToStarMap[toId]

      if (fromStar && toStar) {
        lines.value.push({
          id: `line_${index + 1}`,
          fromStarId: fromStar.id,
          toStarId: toStar.id,
          points: [fromStar.x, fromStar.y, toStar.x, toStar.y],
          stroke: lineStyle.value.stroke,
          strokeWidth: lineStyle.value.strokeWidth,
          dash: lineStyle.value.dash,
          shadowEnabled: lineStyle.value.shadowEnabled,
          shadowColor: lineStyle.value.shadowColor,
          shadowBlur: lineStyle.value.shadowBlur,
          shadowOffsetX: lineStyle.value.shadowOffsetX,
          shadowOffsetY: lineStyle.value.shadowOffsetY,
          opacity: lineStyle.value.opacity
        })
      }
    })
  }

  const updateStarStyle = (style) => {
    // 确保 radius 不小于最小值 2
    if (style.radius !== undefined) {
      style.radius = Math.max(2, style.radius)
    }
    starStyle.value = { ...starStyle.value, ...style }
    // 更新所有星星的样式
    stars.value.forEach(star => {
      if (style.radius !== undefined) {
        star.radius = Math.max(2, style.radius)
      }
      Object.assign(star, style)
    })
  }

  const updateLineStyle = (style) => {
    lineStyle.value = { ...lineStyle.value, ...style }
    // 更新所有连线的样式
    lines.value.forEach(line => {
      Object.assign(line, style)
    })
  }

  const setSelectedStar = (starId) => {
    selectedStarId.value = starId
  }

  const clearCanvas = () => {
    // 清除星星点位数据
    stars.value = []
    lines.value = []
    connections.value = []
    selectedStarId.value = null

    // 清除背景设置，重置为"空(网格)"
    backgroundConfig.value = {
      type: 'grid',
      imageUrl: null,
      color: '#ffffff'
    }
  }

  // 坐标转换工具函数
  const convertRelativeToAbsolute = (relativeData) => {
    const { width, height } = canvasDimensions.value
    return relativeData.map(point => ({
      ...point,
      x: point.x <= 1 ? point.x * width : point.x,
      y: point.y <= 1 ? point.y * height : point.y
    }))
  }

  return {
    // State
    canvasConfig,
    backgroundConfig,
    stars,
    lines,
    starStyle,
    lineStyle,
    selectedStarId,
    
    // Computed
    canvasDimensions,
    
    // Actions
    updateCanvasConfig,
    updateBackgroundConfig,
    setStars,
    updateStarPosition,
    generateLines,
    updateStarStyle,
    updateLineStyle,
    setSelectedStar,
    clearCanvas,
    convertRelativeToAbsolute
  }
})
