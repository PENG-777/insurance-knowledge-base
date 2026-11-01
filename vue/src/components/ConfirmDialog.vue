<template>
  <div class="overlay" @click.self="$emit('cancel')">
    <div class="dialog">
      <div class="dialog-head">
        <div class="dialog-icon" :data-danger="danger">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7.5v5.2M12 16v.3" stroke-linecap="round" />
          </svg>
        </div>
        <div>
          <div class="dialog-title">{{ title }}</div>
          <div class="dialog-msg">{{ message }}</div>
        </div>
      </div>
      <div class="dialog-actions">
        <button class="btn btn-ghost" @click="$emit('cancel')">取消</button>
        <button class="btn" :class="danger ? 'btn-danger' : 'btn-primary'" :disabled="loading" @click="$emit('confirm')">
          {{ loading ? '处理中…' : confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '确认操作' },
  message: { type: String, default: '此操作需要确认，是否继续？' },
  confirmText: { type: String, default: '确认' },
  danger: { type: Boolean, default: false },
  loading: { type: Boolean, default: false }
})

defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 900;
  background: rgba(15, 39, 66, 0.32);
  backdrop-filter: blur(2px);
  display: grid;
  place-items: center;
  padding: 20px;
}

.dialog {
  width: 100%;
  max-width: 410px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid var(--line);
  box-shadow: 0 24px 70px rgba(15, 39, 66, 0.22);
  padding: 22px;
  animation: dialog-in 0.18s ease;
}

.dialog-head {
  display: flex;
  gap: 13px;
  align-items: flex-start;
}

.dialog-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex: none;
  color: var(--gold-deep);
  background: #f8f1df;
}

.dialog-icon[data-danger='true'] {
  color: var(--danger);
  background: var(--danger-soft);
}

.dialog-title {
  font-family: var(--serif);
  font-size: 17px;
  color: var(--ink);
  margin-bottom: 4px;
}

.dialog-msg {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.7;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
}

@keyframes dialog-in {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.98);
  }
}
</style>
