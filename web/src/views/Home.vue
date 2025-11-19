<template>
  <div class="home-container">
    <div class="canvas-area">
      <CanvasComponent />
    </div>
  </div>
</template>

<script setup>
import CanvasComponent from '@/components/CanvasComponent.vue'

</script>

<style scoped>
.home-container {
  height: 100%;
  width: 100%;
  background: #f8f9fa;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow-y: auto;
  padding: 20px;
  padding-top: 30px;
}

.canvas-area {
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}
</style>
