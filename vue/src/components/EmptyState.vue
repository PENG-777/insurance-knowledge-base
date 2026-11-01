<template>
  <div class="empty">
    <div class="empty-art">
      <svg viewBox="0 0 64 64" width="52" height="52" fill="none" stroke="currentColor" stroke-width="1.3">
        <rect x="12" y="18" width="40" height="32" rx="3" />
        <path d="M12 24l20 14 20-14" stroke-linejoin="round" />
        <path d="M25 12h14" stroke-linecap="round" opacity="0.5" />
      </svg>
    </div>
    <div class="empty-title">{{ title }}</div>
    <div class="empty-desc">{{ desc }}</div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无数据' },
  desc: { type: String, default: '当前条件下没有可展示的内容' }
})
</script>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 42px 24px;
  color: var(--muted);
}

.empty-art {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #faf7f0;
  border: 1px solid var(--line);
  color: var(--gold);
  margin-bottom: 14px;
}

.empty-title {
  font-family: var(--serif);
  font-size: 16px;
  color: var(--ink);
  margin-bottom: 5px;
}

.empty-desc {
  font-size: 12.5px;
  max-width: 340px;
  line-height: 1.7;
}

.empty :deep(button) {
  margin-top: 16px;
}
</style>
