<template>
  <aside class="right-sider">
    <div class="right-sidebar-content">

      <!-- 操作按钮 -->
      <div class="section">
        <h3 class="section-title">操作</h3>
        <div class="action-buttons">
          <el-button type="primary" @click="showExportDialog" :icon="Download"> 导出图片 </el-button>
          <el-button @click="resetStyles" type="info" :icon="RefreshLeft" class="!ml-0">重置样式</el-button>
          <el-button @click="clearCanvas" type="danger" :icon="Delete" class="!ml-0">清空画布</el-button>
        </div>
      </div>

      <!-- 导出对话框 -->
      <el-dialog
        v-model="exportDialogVisible"
        title="导出图片"
        width="400px"
        :close-on-click-modal="false"
      >
        <div class="export-dialog-content">
          <div class="export-option-item">
            <label class="export-option-label">导出分辨率</label>
            <el-select v-model="exportPixelRatio" size="default" style="width: 100%;">
              <el-option label="2倍 (标准高清)" :value="2" />
              <el-option label="3倍 (超高清)" :value="3" />
              <el-option label="4倍 (极致高清)" :value="4" />
            </el-select>
          </div>
          <div class="export-option-item">
            <label class="export-option-label">导出格式</label>
            <el-radio-group v-model="exportFormat" class="radio-group-horizontal">
              <el-radio value="png">PNG (无损)</el-radio>
              <el-radio value="jpg">JPG (压缩)</el-radio>
            </el-radio-group>
          </div>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="exportDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="confirmExport">确认导出</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 星星点样式设置 -->
      <div class="section">
        <h3 class="section-title" @click="toggleStarStyle">
          <span>星星点样式</span>
          <el-icon class="collapse-icon" :class="{ 'collapsed': !starStyleExpanded }">
            <ArrowDown v-if="starStyleExpanded" />
            <ArrowUp v-else />
          </el-icon>
        </h3>
        <div v-show="starStyleExpanded">
          <!-- 星星大小 -->
          <div class="style-item">
          <label class="style-label">大小</label>
          <el-slider
            v-model="starRadius"
            :min="2"
            :max="50"
            @change="updateStarStyle"
            show-input
            :show-input-controls="false"
          />
        </div>

        <!-- 星星颜色 - 紧凑布局 -->
        <div class="style-item style-item-inline">
          <label class="style-label">填充颜色</label>
          <el-color-picker v-model="starFill" @change="updateStarStyle" />
        </div>

        <!-- 描边设置 - 紧凑布局 -->
        <div class="style-item style-item-inline">
          <label class="style-label">描边颜色</label>
          <el-color-picker v-model="starStroke" @change="updateStarStyle" />
        </div>

        <div class="style-item">
          <label class="style-label">描边宽度</label>
          <el-slider
            v-model="starStrokeWidth"
            :min="0"
            :max="10"
            @change="updateStarStyle"
            show-input
            :show-input-controls="false"
          />
        </div>

        <!-- 阴影设置 -->
        <div class="style-item style-item-inline">
          <label class="style-label">阴影效果</label>
          <el-switch v-model="starShadowEnabled" @change="updateStarStyle" />
        </div>

        <template v-if="starShadowEnabled">
          <div class="style-item style-item-inline">
            <label class="style-label">阴影颜色</label>
            <el-color-picker v-model="starShadowColor" @change="updateStarStyle" />
          </div>

          <div class="style-item">
            <label class="style-label">阴影模糊度<span class="ml-1 text-xs text-grey-300">(产生光晕效果)</span></label>
            <el-slider
              v-model="starShadowBlur"
              :min="20"
              :max="100"
              @change="updateStarStyle"
              show-input
              :show-input-controls="false"
            />
          </div>

          <div class="style-item">
            <label class="style-label">阴影偏移X</label>
            <el-slider
              v-model="starShadowOffsetX"
              :min="-20"
              :max="20"
              @change="updateStarStyle"
              show-input
              :show-input-controls="false"
            />
          </div>

          <div class="style-item">
            <label class="style-label">阴影偏移Y</label>
            <el-slider
              v-model="starShadowOffsetY"
              :min="-20"
              :max="20"
              @change="updateStarStyle"
              show-input
              :show-input-controls="false"
            />
          </div>
        </template>
        </div>
      </div>

      <!-- 连线样式设置 -->
      <div class="section">
        <h3 class="section-title" @click="toggleLineStyle">
          <span>连线样式</span>
          <el-icon class="collapse-icon" :class="{ 'collapsed': !lineStyleExpanded }">
            <ArrowDown v-if="lineStyleExpanded" />
            <ArrowUp v-else />
          </el-icon>
        </h3>
        <div v-show="lineStyleExpanded">
          <!-- 线条颜色 - 紧凑布局 -->
        <div class="style-item style-item-inline">
          <label class="style-label">线条颜色</label>
          <el-color-picker v-model="lineStroke" @change="updateLineStyle" />
        </div>

        <!-- 线条粗细 -->
        <div class="style-item">
          <label class="style-label">线条粗细</label>
          <el-slider
            v-model="lineStrokeWidth"
            :min="1"
            :max="10"
            @change="updateLineStyle"
            show-input
            :show-input-controls="false"
          />
        </div>

        <!-- 线条类型 -->
        <div class="style-item">
          <label class="style-label">线条类型</label>
          <el-radio-group v-model="lineType" @change="handleLineTypeChange" class="radio-group-horizontal">
            <el-radio value="solid">实线</el-radio>
            <el-radio value="dashed">虚线</el-radio>
          </el-radio-group>
        </div>

        <!-- 虚线间隔 -->
        <div v-if="lineType === 'dashed'" class="style-item">
          <label class="style-label">虚线间隔</label>
          <el-slider
            v-model="lineDashGap"
            :min="1"
            :max="20"
            @change="updateLineStyle"
            show-input
            :show-input-controls="false"
          />
        </div>

        <!-- 阴影设置 - 紧凑布局 -->
        <div class="style-item style-item-inline">
          <label class="style-label">阴影效果</label>
          <el-switch v-model="lineShadowEnabled" @change="updateLineStyle" />
        </div>

        <template v-if="lineShadowEnabled">
          <div class="style-item style-item-inline">
            <label class="style-label">阴影颜色</label>
            <el-color-picker v-model="lineShadowColor" @change="updateLineStyle" />
          </div>

          <div class="style-item">
            <label class="style-label">阴影模糊度</label>
            <el-slider
              v-model="lineShadowBlur"
              :min="20"
              :max="100"
              @change="updateLineStyle"
              show-input
              :show-input-controls="false"
            />
          </div>

          <div class="style-item">
            <label class="style-label">阴影偏移X</label>
            <el-slider
              v-model="lineShadowOffsetX"
              :min="-20"
              :max="20"
              @change="updateLineStyle"
              show-input
              :show-input-controls="false"
            />
          </div>

          <div class="style-item">
            <label class="style-label">阴影偏移Y</label>
            <el-slider
              v-model="lineShadowOffsetY"
              :min="-20"
              :max="20"
              @change="updateLineStyle"
              show-input
              :show-input-controls="false"
            />
          </div>
        </template>
        </div>
      </div>

      
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Download, Delete, RefreshLeft, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCanvasStore } from '@/stores/canvas'
import defaultStyles from '@/stores/defaultStyles.json'

const canvasStore = useCanvasStore()

// 折叠状态 - 默认全部展开
const starStyleExpanded = ref(true)
const lineStyleExpanded = ref(true)

// 星星样式响应式数据 - 从 store 读取默认值
const starRadius = ref(canvasStore.starStyle.radius)
const starFill = ref(canvasStore.starStyle.fill)
const starStroke = ref(canvasStore.starStyle.stroke)
const starStrokeWidth = ref(canvasStore.starStyle.strokeWidth)
const starShadowEnabled = ref(canvasStore.starStyle.shadowEnabled)
const starShadowColor = ref(canvasStore.starStyle.shadowColor)
const starShadowBlur = ref(canvasStore.starStyle.shadowBlur)
const starShadowOffsetX = ref(canvasStore.starStyle.shadowOffsetX)
const starShadowOffsetY = ref(canvasStore.starStyle.shadowOffsetY)

// 连线样式响应式数据 - 从 store 读取默认值
const lineStroke = ref(canvasStore.lineStyle.stroke)
const lineStrokeWidth = ref(canvasStore.lineStyle.strokeWidth)
const lineType = ref('solid')
const lineDashGap = ref(5)
const lineShadowEnabled = ref(canvasStore.lineStyle.shadowEnabled)
const lineShadowColor = ref(canvasStore.lineStyle.shadowColor)
const lineShadowBlur = ref(canvasStore.lineStyle.shadowBlur)
const lineShadowOffsetX = ref(canvasStore.lineStyle.shadowOffsetX)
const lineShadowOffsetY = ref(canvasStore.lineStyle.shadowOffsetY)

// 监听 store 变化，同步到 UI
watch(() => canvasStore.starStyle, (newStyle) => {
  starRadius.value = newStyle.radius
  starFill.value = newStyle.fill
  starStroke.value = newStyle.stroke
  starStrokeWidth.value = newStyle.strokeWidth
  starShadowEnabled.value = newStyle.shadowEnabled
  starShadowColor.value = newStyle.shadowColor
  starShadowBlur.value = newStyle.shadowBlur
  starShadowOffsetX.value = newStyle.shadowOffsetX
  starShadowOffsetY.value = newStyle.shadowOffsetY
}, { deep: true })

watch(() => canvasStore.lineStyle, (newStyle) => {
  lineStroke.value = newStyle.stroke
  lineStrokeWidth.value = newStyle.strokeWidth
  lineShadowEnabled.value = newStyle.shadowEnabled
  lineShadowColor.value = newStyle.shadowColor
  lineShadowBlur.value = newStyle.shadowBlur
  lineShadowOffsetX.value = newStyle.shadowOffsetX
  lineShadowOffsetY.value = newStyle.shadowOffsetY
}, { deep: true })

// 导出选项
const exportDialogVisible = ref(false)
const exportPixelRatio = ref(3)
const exportFormat = ref('png')

// 方法
const updateStarStyle = () => {
  const style = {
    radius: starRadius.value,
    fill: starFill.value,
    stroke: starStroke.value,
    strokeWidth: starStrokeWidth.value,
    shadowEnabled: starShadowEnabled.value,
    shadowColor: starShadowColor.value,
    shadowBlur: starShadowBlur.value,
    shadowOffsetX: starShadowOffsetX.value,
    shadowOffsetY: starShadowOffsetY.value
  }
  canvasStore.updateStarStyle(style)
}

const updateLineStyle = () => {
  const dash = lineType.value === 'dashed' ? [lineDashGap.value, lineDashGap.value] : []
  const style = {
    stroke: lineStroke.value,
    strokeWidth: lineStrokeWidth.value,
    dash: dash,
    shadowEnabled: lineShadowEnabled.value,
    shadowColor: lineShadowColor.value,
    shadowBlur: lineShadowBlur.value,
    shadowOffsetX: lineShadowOffsetX.value,
    shadowOffsetY: lineShadowOffsetY.value
  }
  canvasStore.updateLineStyle(style)
}

const handleLineTypeChange = () => {
  updateLineStyle()
}

const resetStyles = () => {
  // 从 JSON 配置重置星星样式
  canvasStore.updateStarStyle({
    ...defaultStyles.star
  })

  // 从 JSON 配置重置连线样式
  canvasStore.updateLineStyle({
    ...defaultStyles.line
  })

  // 重置线条类型
  lineType.value = 'solid'
  lineDashGap.value = 5

  ElMessage.success('样式已重置为默认值')
}

const showExportDialog = () => {
  exportDialogVisible.value = true
}

const confirmExport = () => {
  exportDialogVisible.value = false
  const event = new CustomEvent('export-canvas', {
    detail: {
      pixelRatio: exportPixelRatio.value,
      mimeType: exportFormat.value === 'png' ? 'image/png' : 'image/jpeg',
      quality: 0.95
    }
  })
  window.dispatchEvent(event)
}

const clearCanvas = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空画布吗？此操作不可撤销。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    canvasStore.clearCanvas()
    ElMessage.success('画布已清空')
  } catch {
    // 用户取消操作
  }
}

// 折叠切换方法
const toggleStarStyle = () => {
  starStyleExpanded.value = !starStyleExpanded.value
}

const toggleLineStyle = () => {
  lineStyleExpanded.value = !lineStyleExpanded.value
}

// 初始化样式
updateStarStyle()
updateLineStyle()
</script>

<style scoped>
.right-sider {
  width: 250px;
  background: white;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
}

.right-sidebar-content {
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

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.style-label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

:deep(.el-slider) {
  margin-top: 5px;
}

:deep(.el-slider__input) {
  width: 60px;
}

:deep(.el-color-picker) {
  margin-top: 5px;
}

:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 5px;
}

:deep(.el-radio) {
  margin-right: 0;
}

/* 横向排列的 radio-group */
:deep(.radio-group-horizontal) {
  flex-direction: row;
  gap: 15px;
  margin-top: 5px;
}

:deep(.radio-group-horizontal .el-radio) {
  margin-right: 0;
}

:deep(.el-switch) {
  margin-top: 5px;
}

/* 紧凑布局样式 */
.style-item {
  margin-bottom: 12px;
}

.style-item:last-child {
  margin-bottom: 0;
}

.style-item-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.style-item-inline .style-label {
  margin-bottom: 0;
  margin-right: 10px;
}

.style-item-inline :deep(.el-color-picker) {
  margin-top: 0;
}

.style-item-inline :deep(.el-switch) {
  margin-top: 0;
}

/* 导出对话框样式 */
.export-dialog-content {
  padding: 10px 0;
}

.export-option-item {
  margin-bottom: 20px;
}

.export-option-item:last-child {
  margin-bottom: 0;
}

.export-option-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}
</style>
