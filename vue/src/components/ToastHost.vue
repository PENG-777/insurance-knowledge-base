<template>
  <div class="toast-host">
    <transition-group name="toast">
      <div v-for="item in toasts" :key="item.id" class="toast" :data-type="item.type">
        <span class="toast-icon">
          <svg v-if="item.type === 'success'" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M3 8.5l3 3 7-7" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <svg v-else-if="item.type === 'error'" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M4 4l8 8M12 4l-8 8" stroke-linecap="round" />
          </svg>
          <svg v-else viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8">
            <circle cx="8" cy="8" r="6" />
            <path d="M8 5v4M8 11.5v.2" stroke-linecap="round" />
          </svg>
        </span>
        <span class="toast-text">{{ item.message }}</span>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useToast } from '../composables/useToast'

const { toasts } = useToast()
</script>

<style scoped>
.toast-host {
  position: fixed;
  right: 22px;
  bottom: 22px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  min-width: 220px;
  max-width: 380px;
  padding: 12px 15px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: 0 12px 30px rgba(15, 39, 66, 0.14);
  font-size: 13px;
  color: var(--text);
  line-height: 1.5;
}

.toast[data-type='success'] {
  border-left: 3px solid var(--success);
}

.toast[data-type='error'] {
  border-left: 3px solid var(--danger);
}

.toast[data-type='info'] {
  border-left: 3px solid var(--ink-3);
}

.toast-icon {
  margin-top: 2px;
  color: var(--success);
  flex: none;
}

.toast[data-type='error'] .toast-icon {
  color: var(--danger);
}

.toast[data-type='info'] .toast-icon {
  color: var(--ink-3);
}

.toast-text {
  flex: 1;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
</style>
