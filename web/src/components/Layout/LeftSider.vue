<template>
  <aside class="left-sider">
    <div class="left-sidebar-content">
      <!-- 画布大小设置 -->
      <div class="section">
        <h3 class="section-title" @click="toggleCanvasConfig">
          <span>画布设置</span>
          <el-icon class="collapse-icon" :class="{ 'collapsed': !canvasConfigExpanded }">
            <ArrowDown v-if="canvasConfigExpanded" />
            <ArrowUp v-else />
          </el-icon>
        </h3>
        <div v-show="canvasConfigExpanded" class="canvas-size-options">
          <el-radio-group v-model="selectedAspectRatio" @change="handleAspectRatioChange">
            <el-radio value="9:16">竖屏 (9:16)</el-radio>
            <el-radio value="3:4">标准 (3:4)</el-radio>
            <el-radio value="1:1">正方形 (1:1)</el-radio>
            <el-radio value="auto">自适应</el-radio>
          </el-radio-group>
        </div>
      </div>

      <!-- 背景设置 -->
      <div class="section">
        <h3 class="section-title" @click="toggleBackgroundConfig">
          <span>背景设置</span>
          <el-icon class="collapse-icon" :class="{ 'collapsed': !backgroundConfigExpanded }">
            <ArrowDown v-if="backgroundConfigExpanded" />
            <ArrowUp v-else />
          </el-icon>
        </h3>
        <div v-show="backgroundConfigExpanded">
          <!-- 背景类型选择 -->
          <div class="background-type-selector">
            <el-radio-group v-model="backgroundType" @change="handleBackgroundTypeChange">
              <el-radio value="grid">空 (网格)</el-radio>
              <el-radio value="image">图片</el-radio>
              <el-radio value="color">纯色</el-radio>
            </el-radio-group>
          </div>

          <!-- 图片上传 -->
          <div v-if="backgroundType === 'image'" class="background-image-section">
            <el-upload
              class="image-uploader"
              :show-file-list="false"
              :on-success="handleImageSuccess"
              :before-upload="beforeImageUpload"
              action="#"
              :http-request="handleImageUpload"
            >
              <div class="upload-content">
                <img v-if="backgroundImageUrl && !imageUploading" :src="backgroundImageUrl" class="uploaded-image" />
                <el-icon v-else-if="!imageUploading" class="image-uploader-icon"><Plus /></el-icon>
                <div v-if="imageUploading" class="upload-loading">
                  <el-icon class="loading-icon"><Loading /></el-icon>
                  <span class="loading-text">上传中...</span>
                </div>
              </div>
            </el-upload>
            <div class="upload-tip">支持 JPG、PNG 格式，最大 5MB</div>
          </div>

          <!-- 纯色选择 -->
          <div v-if="backgroundType === 'color'" class="background-color-section">
            <span class="text-sm mx-2 style-label !inline">选择背景颜色</span>
            <el-color-picker v-model="backgroundColor" @change="handleBackgroundColorChange" />
          </div>
        </div>
      </div>

      <!-- 星星点位输入 -->
      <div class="section">
        <div>
          <h3 class="section-title">星星点位数据</h3>
        </div>
        
        <!-- JSON输入框 -->
        <div class="json-input-section">
          <el-input
            v-model="jsonInput"
            type="textarea"
            :rows="14"
            placeholder="请输入JSON格式的星星点位数据"
            :class="{ 'input-error': jsonError }"
          />
          <div v-if="jsonError" class="error-message">{{ jsonError }}</div>
          <!-- 示例数据 -->
          <div class="text-right">
            <el-button text @click="loadExample">加载示例数据</el-button>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button type="primary" @click="generateStars" :disabled="!jsonInput.trim()">
            生成星星
          </el-button>
          <el-button @click="clearInput">清空</el-button>
        </div>

      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus, ArrowDown, ArrowUp, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useCanvasStore } from '@/stores/canvas'

const canvasStore = useCanvasStore()

// 响应式数据
const selectedAspectRatio = ref('9:16')
const backgroundType = ref('grid')
const backgroundImageUrl = ref('')
const backgroundColor = ref('#ffffff')
const jsonInput = ref('')
const jsonError = ref('')
const imageUploading = ref(false)

// 折叠状态 - 默认全部展开
const canvasConfigExpanded = ref(true)
const backgroundConfigExpanded = ref(true)

// 示例数据
const exampleData = `{
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
}`

// 方法
const handleAspectRatioChange = (value) => {
  canvasStore.updateCanvasConfig({ aspectRatio: value })
}

const handleBackgroundTypeChange = (type) => {
  if (type === 'color') {
    // 切换到纯色时，设置默认背景色为 #2f303d
    backgroundColor.value = '#2f303d'
    canvasStore.updateBackgroundConfig({
      type: 'color',
      color: '#2f303d'
    })
  } else {
    canvasStore.updateBackgroundConfig({ type })
  }
  if (type !== 'image') {
    backgroundImageUrl.value = ''
    imageUploading.value = false
  }
}

const handleImageUpload = (options) => {
  const file = options.file
  const reader = new FileReader()
  
  // 开始上传，显示loading
  imageUploading.value = true

  reader.onload = (e) => {
    backgroundImageUrl.value = e.target.result
    canvasStore.updateBackgroundConfig({
      type: 'image',
      imageUrl: e.target.result
    })
    
    // 如果选择了自适应，更新画布尺寸
    if (selectedAspectRatio.value === 'auto') {
      const img = new Image()
      img.onload = () => {
        canvasStore.updateCanvasConfig({
          width: img.width,
          height: img.height
        })
        // 图片加载完成，隐藏loading
        imageUploading.value = false
      }
      img.onerror = () => {
        // 图片加载失败，隐藏loading
        imageUploading.value = false
        ElMessage.error('图片加载失败')
      }
      img.src = e.target.result
    } else {
      // 非自适应模式，直接隐藏loading
      imageUploading.value = false
    }
  }
  
  reader.onerror = () => {
    // 文件读取失败，隐藏loading
    imageUploading.value = false
    ElMessage.error('图片读取失败')
  }

  reader.readAsDataURL(file)
  return false // 阻止默认上传行为
}

const handleImageSuccess = () => {
  ElMessage.success('图片上传成功')
}

const beforeImageUpload = (file) => {
  const isValidType = file.type === 'image/jpeg' || file.type === 'image/png'
  const isValidSize = file.size / 1024 / 1024 < 5

  if (!isValidType) {
    ElMessage.error('只支持 JPG 和 PNG 格式的图片')
    return false
  }
  if (!isValidSize) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

const handleBackgroundColorChange = (color) => {
  console.log(color)
  canvasStore.updateBackgroundConfig({
    type: 'color',
    color: color
  })
}

const validateJSON = (jsonStr) => {
  try {
    const data = JSON.parse(jsonStr)
    
    if (!data || typeof data !== 'object') {
      return '数据必须是对象格式'
    }

    if (!Array.isArray(data.points)) {
      return '数据必须包含 points 数组'
    }

    if (!Array.isArray(data.connections)) {
      return '数据必须包含 connections 数组'
    }

    // 验证 points
    for (let i = 0; i < data.points.length; i++) {
      const point = data.points[i]
      if (typeof point.id !== 'number') {
        return `points[${i}] 缺少有效的 id`
      }
      if (typeof point.x !== 'number' || typeof point.y !== 'number') {
        return `points[${i}] 缺少有效的 x 或 y 坐标`
      }
    }

    // 验证 connections
    for (let i = 0; i < data.connections.length; i++) {
      const conn = data.connections[i]
      if (!Array.isArray(conn) || conn.length !== 2) {
        return `connections[${i}] 格式错误，应为 [id1, id2] 格式`
      }
      if (typeof conn[0] !== 'number' || typeof conn[1] !== 'number') {
        return `connections[${i}] 中的 id 必须是数字`
      }
      // 验证连接的点是否存在
      const pointIds = data.points.map(p => p.id)
      if (!pointIds.includes(conn[0]) || !pointIds.includes(conn[1])) {
        return `connections[${i}] 引用了不存在的点 id`
      }
    }

    return null
  } catch (error) {
    return 'JSON 格式错误'
  }
}

const generateStars = () => {
  const error = validateJSON(jsonInput.value)
  if (error) {
    jsonError.value = error
    ElMessage.error(error)
    return
  }
  
  jsonError.value = ''
  
  try {
    const data = JSON.parse(jsonInput.value)
    // 转换 points 中的相对坐标为绝对坐标
    const convertedPoints = canvasStore.convertRelativeToAbsolute(data.points)
    // 传递 points 和 connections 给 store
    canvasStore.setStars(convertedPoints, data.connections)
    ElMessage.success(`成功生成 ${data.points.length} 个星星`)
  } catch (error) {
    ElMessage.error('生成星星失败')
  }
}

const clearInput = () => {
  jsonInput.value = ''
  jsonError.value = ''
  canvasStore.clearCanvas()
}

const loadExample = () => {
  jsonInput.value = exampleData
  jsonError.value = ''
}

// 折叠切换方法
const toggleCanvasConfig = () => {
  canvasConfigExpanded.value = !canvasConfigExpanded.value
}

const toggleBackgroundConfig = () => {
  backgroundConfigExpanded.value = !backgroundConfigExpanded.value
}

// 监听JSON输入变化，实时验证
watch(jsonInput, (newValue) => {
  if (newValue.trim()) {
    jsonError.value = validateJSON(newValue) || ''
  } else {
    jsonError.value = ''
  }
})

// 监听背景配置变化，同步到本地状态
watch(() => canvasStore.backgroundConfig, (newConfig) => {
  backgroundType.value = newConfig.type
  backgroundImageUrl.value = newConfig.imageUrl || ''
  backgroundColor.value = newConfig.color || '#ffffff'
}, { deep: true })

// 监听星星数据变化，当画布被清空时，同时清空输入框
watch(() => canvasStore.stars, (newStars) => {
  if (newStars.length === 0 && jsonInput.value.trim()) {
    jsonInput.value = ''
    jsonError.value = ''
  }
})

// 初始化
canvasStore.updateCanvasConfig({ aspectRatio: selectedAspectRatio.value })
canvasStore.updateBackgroundConfig({ type: backgroundType.value })
</script>

<style scoped>
.left-sider {
  width: 350px;
  background: white;
  border-right: 1px solid #e4e7ed;
  overflow-y: auto;
}

.left-sidebar-content {
  padding: 20px;
}

.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
  border-bottom: 2px solid var(--el-color-primary);
  padding-bottom: 5px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.section-title:hover {
  color: var(--el-color-primary);
}

.collapse-icon {
  font-size: 14px;
  color: #909399;
  transition: transform 0.3s, color 0.2s;
}

.section-title:hover .collapse-icon {
  color: var(--el-color-primary);
}

.canvas-size-options {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 10px;
}

.background-type-selector {
  margin-bottom: 15px;
  display: flex;
  flex-direction: row;
}

.background-image-section {
  margin-top: 15px;
}

.image-uploader {
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.image-uploader:hover {
  border-color: var(--el-color-primary);
}

.image-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 309px;
  height: 120px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-content {
  position: relative;
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.uploaded-image {
  /* width: 309px; */
  height: 120px;
  object-fit: cover;
  display: block;
}

.upload-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.9);
}

.loading-icon {
  font-size: 32px;
  color: var(--el-color-primary);
  animation: rotating 2s linear infinite;
}

.loading-text {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.upload-tip {
  font-size: 12px;
  color: #606266;
  margin-top: 8px;
}

.background-color-section {
  margin-top: 15px;
}

.json-input-section {
  margin-bottom: 15px;
}

.input-error {
  border-color: #f56c6c !important;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

:deep(.el-radio) {
  margin-bottom: 0;
  margin-right: 15px;
}

:deep(.el-radio-group) {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
}

:deep(.el-upload) {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

:deep(.el-upload:hover) {
  border-color: var(--el-color-primary);
}
</style>
