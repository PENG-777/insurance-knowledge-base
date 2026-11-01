<template>
  <span class="badge" :data-tone="meta.tone" :class="size">
    <span class="dot"></span>{{ meta.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'doc' },
  value: { type: String, default: '' },
  label: { type: String, default: '' },
  size: { type: String, default: '' }
})

const MAPS = {
  doc: {
    uploaded: { label: '待处理', tone: 'gray' },
    processing: { label: '处理中', tone: 'blue' },
    review: { label: '待复核', tone: 'amber' },
    published: { label: '已发布', tone: 'green' },
    failed: { label: '失败', tone: 'red' }
  },
  run: {
    running: { label: '执行中', tone: 'blue' },
    success: { label: '完成', tone: 'green' },
    failed: { label: '失败', tone: 'red' },
    pending: { label: '待执行', tone: 'gray' }
  },
  level: {
    P0: { label: 'P0 紧急', tone: 'red' },
    P1: { label: 'P1 重要', tone: 'amber' },
    P2: { label: 'P2 建议', tone: 'blue' }
  },
  risk: {
    低: { label: '低风险', tone: 'green' },
    中: { label: '中风险', tone: 'amber' },
    高: { label: '高风险', tone: 'red' },
    待评估: { label: '待评估', tone: 'gray' },
    safe: { label: '未命中', tone: 'green' },
    warn: { label: '需提示', tone: 'amber' },
    block: { label: '已拦截', tone: 'red' }
  },
  mode: {
    llm: { label: 'DeepSeek', tone: 'gold' },
    mock: { label: '本地规则', tone: 'blue' }
  },
  entity: {
    pending: { label: '待复核', tone: 'amber' },
    approved: { label: '已确认', tone: 'green' },
    rejected: { label: '已驳回', tone: 'red' }
  }
}

const meta = computed(() => {
  const map = MAPS[props.type] || {}
  if (props.label) return { label: props.label, tone: props.value || 'gray' }
  return map[props.value] || { label: props.value || '未知', tone: 'gray' }
})
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border-radius: 5px;
  font-size: 11.5px;
  line-height: 1.7;
  white-space: nowrap;
  border: 1px solid transparent;
}

.badge.sm {
  font-size: 11px;
  padding: 1px 6px;
}

.badge[data-tone='green'] {
  color: var(--success);
  background: var(--success-soft);
  border-color: #cfe7dc;
}

.badge[data-tone='red'] {
  color: var(--danger);
  background: var(--danger-soft);
  border-color: #efd0c7;
}

.badge[data-tone='amber'] {
  color: var(--warn);
  background: var(--warn-soft);
  border-color: #efdfba;
}

.badge[data-tone='blue'] {
  color: var(--info);
  background: var(--info-soft);
  border-color: #d6e3ef;
}

.badge[data-tone='gold'] {
  color: #7b5d20;
  background: #f7efdc;
  border-color: #e8d8b4;
}

.badge[data-tone='gray'] {
  color: var(--muted);
  background: #f3f1ec;
  border-color: #e7e2d8;
}
</style>
