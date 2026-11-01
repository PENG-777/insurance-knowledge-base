<template>
  <div class="skeleton-lines">
    <div
      v-for="line in lines"
      :key="line"
      class="skeleton"
      :style="{ height: height, width: widths[(line - 1) % widths.length] }"
    ></div>
  </div>
</template>

<script setup>
defineProps({
  lines: { type: Number, default: 4 },
  height: { type: String, default: '14px' }
})

const widths = ['100%', '92%', '78%', '96%', '64%']
</script>

<style scoped>
.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: 11px;
  padding: 6px 0;
}
</style>
