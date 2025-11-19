<template>
  <div class="layout-container">
    <Header />
    <div class="layout-content">
      <LeftSider />
      <Main />
      <RightSider />
    </div>
  </div>
</template>

<script setup>
import Header from './Header.vue'
import LeftSider from './LeftSider.vue'
import Main from './Main.vue'
import RightSider from './RightSider.vue'
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.layout-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}
</style>
