<template>
  <main class="main-content">
    <router-view />
  </main>
</template>

<script setup>
</script>

<style scoped>
.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f8f9fa;
  min-width: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
</style>
