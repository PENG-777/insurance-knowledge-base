<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">Human-in-the-loop Review</div>
        <h1 class="page-title">复核工作台</h1>
        <div class="page-sub">P0/P1 全部通过后方可发布 · 抽取字段可人工校正 · 全过程留痕审计</div>
      </div>
      <div class="page-actions">
        <router-link to="/documents" class="btn btn-ghost">返回文档中心</router-link>
      </div>
    </div>

    <section v-if="stats" class="grid-4 stats">
      <div class="card stat-card">
        <div class="stat-top"><span class="stat-label">待复核任务</span><span class="chip">P0 {{ stats.levels.P0.pending }}</span></div>
        <div class="stat-value" :class="{ danger: stats.pending_total > 0 }">{{ stats.pending_total }}</div>
        <div class="stat-sub">P1 {{ stats.levels.P1.pending }} · P2 {{ stats.levels.P2.pending }}</div>
      </div>
      <div class="card stat-card">
        <div class="stat-top"><span class="stat-label">今日已完成</span><span class="stat-tag">人机协同</span></div>
        <div class="stat-value">{{ stats.today_resolved }}</div>
        <div class="stat-sub">累计完成 {{ stats.resolved_total }} 项复核</div>
      </div>
      <div class="card stat-card">
        <div class="stat-top"><span class="stat-label">平均复核耗时</span><span class="stat-tag">效率</span></div>
        <div class="stat-value">{{ stats.avg_resolution_minutes }}<small>分钟</small></div>
        <div class="stat-sub">从任务生成到人工确认</div>
      </div>
      <div class="card stat-card">
        <div class="stat-top"><span class="stat-label">待复核文档</span><span class="stat-tag">发布闸门</span></div>
        <div class="stat-value">{{ stats.documents_waiting }}</div>
        <div class="stat-sub">清理 P0/P1 后自动发布</div>
      </div>
    </section>

    <section class="tabs card">
      <button
        v-for="tab in tabs"
        :key="tab.level"
        class="tab"
        :class="{ active: tab.level === level }"
        @click="switchLevel(tab.level)"
      >
        <StatusBadge type="level" :value="tab.level" size="sm" />
        <span class="tab-count">{{ tab.pending }}</span>
        <span class="tab-desc">{{ tab.desc }}</span>
      </button>
    </section>

    <section v-if="loading" class="grid-2 review-grid">
      <div class="card card-pad"><SkeletonBlock :lines="9" /></div>
      <div class="card card-pad"><SkeletonBlock :lines="7" /></div>
    </section>

    <section v-else-if="current" class="grid-2 review-grid">
      <div class="card source-card">
        <div class="card-head">
          <div>
            <div class="card-title"><span class="rule"></span>原文依据</div>
            <div class="card-sub" style="margin-top: 5px">{{ current.document_title }}</div>
          </div>
          <div class="source-nav">
            <span>第 {{ index + 1 }} / {{ tasks.length }} 条</span>
            <button class="nav-btn" :disabled="index === 0" title="上一条" @click="move(-1)">
              <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M10 3L5 8l5 5" stroke-linecap="round" /></svg>
            </button>
            <button class="nav-btn" :disabled="index >= tasks.length - 1" title="下一条" @click="move(1)">
              <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 3l5 5-5 5" stroke-linecap="round" /></svg>
            </button>
          </div>
        </div>

        <div class="source-meta">
          <StatusBadge type="level" :value="current.level" size="sm" />
          <span class="chip">{{ current.object_type }}</span>
          <router-link :to="`/documents/${current.document_id}`" class="doc-link">查看文档 →</router-link>
        </div>

        <div class="reason" :data-tone="current.level">
          <span class="reason-label">触发原因</span>
          <span>{{ current.trigger_reason }}</span>
        </div>

        <div class="source-body">
          <div class="source-heading">
            <span v-if="current.section_title">{{ current.section_title }}</span>
            <span v-else>文档级复核</span>
          </div>
          <div class="source-text">{{ current.section_content || '该任务为文档级复核，无对应章节正文。' }}</div>
          <div v-if="current.source_text" class="excerpt">
            <div class="excerpt-label">抽取命中的原文摘录</div>
            <div class="excerpt-text">{{ current.source_text }}</div>
          </div>
        </div>

        <div class="source-foot">
          <span class="conf-label">抽取置信度</span>
          <div class="progress conf-bar" :class="confidenceTone">
            <span :style="{ width: (current.confidence || 0) * 100 + '%' }"></span>
          </div>
          <strong class="conf-value">{{ current.confidence == null ? '—' : Math.round(current.confidence * 100) + '%' }}</strong>
        </div>
      </div>

      <div class="card form-card">
        <div class="card-head">
          <div>
            <div class="card-title">
              <span class="rule"></span>抽取字段
              <span v-if="changedCount" class="changed-count">{{ changedCount }} 项已修改</span>
            </div>
            <div class="card-sub" style="margin-top: 5px">{{ current.entity_name || current.object_type }} · 通过后将写回知识底座</div>
          </div>
        </div>

        <div class="form-body">
          <div v-if="!fieldKeys.length" class="no-fields">该任务未携带结构化字段，可直接确认或驳回。</div>
          <div v-for="key in fieldKeys" :key="key" class="field">
            <label class="field-label" :for="`field-${key}`">{{ key }}</label>
            <textarea
              v-if="isLongField(key)"
              :id="`field-${key}`"
              v-model="draft[key]"
              class="textarea field-area"
              :class="{ edited: isEdited(key) }"
              rows="3"
            ></textarea>
            <input
              v-else
              :id="`field-${key}`"
              v-model="draft[key]"
              class="input"
              :class="{ edited: isEdited(key) }"
            />
          </div>

          <div class="field note-field">
            <label class="field-label" for="review-note">复核意见</label>
            <textarea
              id="review-note"
              v-model="note"
              class="textarea"
              placeholder="通过可留空；驳回必须填写具体原因与修正建议。"
              rows="3"
            ></textarea>
          </div>

          <div v-if="error" class="form-error">{{ error }}</div>
        </div>

        <div class="form-actions">
          <button class="btn btn-danger" :disabled="busy" @click="submit('reject')">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4l8 8M12 4l-8 8" stroke-linecap="round" /></svg>
            驳回
          </button>
          <button class="btn btn-success" :disabled="busy" @click="submit('approve')">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 8.5l3.2 3.2L13 5" stroke-linecap="round" stroke-linejoin="round" /></svg>
            {{ busy ? '提交中…' : '通过并写回' }}
          </button>
        </div>
      </div>
    </section>

    <section v-else class="card">
      <EmptyState
        :title="`${level} 队列已清空`"
        desc="当前级别没有待复核任务。可切换其他级别，或等待流水线生成新的复核项。"
      >
        <button v-if="nextLevel" class="btn btn-ghost" @click="switchLevel(nextLevel)">查看 {{ nextLevel }} 队列</button>
      </EmptyState>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import api from '../api'
import EmptyState from '../components/EmptyState.vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { toast } from '../composables/useToast'

const LEVEL_DESC = { P0: '关键字段 / 数值缺失', P1: '隐式接口 / 低置信度', P2: '表述优化建议' }
const ARRAY_FIELDS = ['关键数值', '模糊表述']

const level = ref('P0')
const stats = ref(null)
const tasks = ref([])
const total = ref(0)
const index = ref(0)
const loading = ref(true)
const busy = ref(false)
const note = ref('')
const error = ref('')
const draft = ref({})
const original = ref({})

const current = computed(() => tasks.value[index.value] || null)
const fieldKeys = computed(() => Object.keys(current.value?.fields || {}))

const tabs = computed(() => {
  const levels = (stats.value && stats.value.levels) || {}
  return ['P0', 'P1', 'P2'].map((item) => ({
    level: item,
    pending: (levels[item] && levels[item].pending) || 0,
    desc: LEVEL_DESC[item]
  }))
})

const nextLevel = computed(() => {
  const pending = tabs.value.find((tab) => tab.level !== level.value && tab.pending > 0)
  return pending ? pending.level : ''
})

const changedCount = computed(() => fieldKeys.value.filter((key) => isEdited(key)).length)

const confidenceTone = computed(() => {
  const value = current.value?.confidence || 0
  if (value < 0.7) return 'danger'
  if (value < 0.85) return 'gold'
  return 'success'
})

function isLongField(key) {
  return key === '原文摘录' || key === '模糊表述' || (draft.value[key] || '').length > 60
}

function isEdited(key) {
  return (draft.value[key] || '') !== (original.value[key] || '')
}

function resetDraft(task) {
  const next = {}
  Object.entries((task && task.fields) || {}).forEach(([key, value]) => {
    if (Array.isArray(value)) next[key] = value.join('、')
    else if (value === null || value === undefined) next[key] = ''
    else if (typeof value === 'object') next[key] = JSON.stringify(value)
    else next[key] = String(value)
  })
  draft.value = next
  original.value = { ...next }
  note.value = ''
  error.value = ''
}

async function loadStats() {
  stats.value = await api.getReviewStats()
}

async function loadTasks(preserve = false) {
  const data = await api.getReviewTasks({ level: level.value, status: 'pending' })
  tasks.value = data.items
  total.value = data.total
  const maxIndex = Math.max(0, tasks.value.length - 1)
  index.value = preserve ? Math.min(index.value, maxIndex) : 0
  resetDraft(current.value)
}

async function refresh(preserve = false) {
  loading.value = true
  try {
    await Promise.all([loadStats(), loadTasks(preserve)])
  } catch (err) {
    toast(err.message, 'error')
  } finally {
    loading.value = false
  }
}

function switchLevel(target) {
  if (target === level.value && tasks.value.length) return
  level.value = target
  index.value = 0
  refresh(false)
}

function move(step) {
  const next = index.value + step
  if (next < 0 || next >= tasks.value.length) return
  index.value = next
  resetDraft(current.value)
}

function collectChanges() {
  const changes = {}
  fieldKeys.value.forEach((key) => {
    if (!isEdited(key)) return
    const raw = draft.value[key] || ''
    if (ARRAY_FIELDS.includes(key)) {
      changes[key] = raw
        .split(/[，,、\n]/)
        .map((item) => item.trim())
        .filter(Boolean)
    } else {
      changes[key] = raw.trim()
    }
  })
  return changes
}

async function submit(action) {
  if (!current.value || busy.value) return
  if (action === 'reject' && !note.value.trim()) {
    error.value = '驳回必须填写复核意见，请说明需修正的字段与原因。'
    return
  }
  error.value = ''
  busy.value = true
  try {
    const changes = collectChanges()
    await api.resolveTask(current.value.id, {
      action,
      note: note.value.trim(),
      corrected_fields: action === 'approve' && Object.keys(changes).length ? changes : null
    })
    toast(action === 'approve' ? '复核已通过，字段已写回知识底座' : '已驳回，该知识对象等待修正', action === 'approve' ? 'success' : 'error')
    await refresh(true)
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

onMounted(() => refresh(false))
</script>

<style scoped>
.stats {
  margin-bottom: 18px;
}

.stat-card {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.stat-tag {
  font-size: 10px;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2px 6px;
  background: #fbf9f4;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.stat-value small {
  font-family: var(--sans);
  font-size: 11px;
  color: var(--faint);
}

.stat-value.danger {
  color: var(--danger);
}

.stat-sub {
  font-size: 11px;
  color: var(--faint);
}

.tabs {
  display: flex;
  padding: 8px;
  gap: 6px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.tab {
  flex: 1;
  min-width: 190px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 9px;
  padding: 10px 13px;
  text-align: left;
  transition: all 0.16s ease;
}

.tab:hover {
  background: #fbf9f4;
}

.tab.active {
  background: #f7f3e8;
  border-color: #e8d8b4;
}

.tab-count {
  font-family: var(--serif);
  font-size: 17px;
  color: var(--ink);
  margin-left: auto;
}

.tab-desc {
  font-size: 10.5px;
  color: var(--faint);
}

.review-grid {
  align-items: start;
}

.source-card,
.form-card {
  display: flex;
  flex-direction: column;
}

.source-card {
  min-height: 540px;
}

.form-card {
  position: sticky;
  top: 18px;
}

.source-nav {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--muted);
}

.nav-btn {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink-2);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.source-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  flex-wrap: wrap;
}

.doc-link {
  font-size: 11.5px;
  color: var(--gold-deep);
  margin-left: auto;
}

.reason {
  margin: 0 22px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  border-left: 3px solid var(--gold);
  background: #fbf7ec;
  border-radius: 0 8px 8px 0;
  padding: 10px 12px;
  font-size: 12px;
  color: #6d5a2f;
  line-height: 1.65;
}

.reason[data-tone='P0'] {
  border-color: var(--danger);
  background: var(--danger-soft);
  color: #8c3a28;
}

.reason-label {
  flex: none;
  font-weight: 600;
}

.source-body {
  padding: 18px 22px 8px;
  flex: 1;
}

.source-heading {
  font-family: var(--serif);
  font-size: 16px;
  color: var(--ink);
  margin-bottom: 10px;
}

.source-text {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.95;
  color: #2b3a49;
  background: #fcfaf5;
  border: 1px solid var(--line-soft);
  border-radius: 9px;
  padding: 14px 16px;
  max-height: 330px;
  overflow-y: auto;
}

.excerpt {
  margin-top: 12px;
  padding: 11px 14px;
  border: 1px dashed #e3d7bd;
  border-radius: 9px;
  background: #fdfbf5;
}

.excerpt-label {
  font-size: 10.5px;
  color: var(--gold-deep);
  letter-spacing: 0.04em;
  margin-bottom: 5px;
}

.excerpt-text {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.75;
  white-space: pre-wrap;
}

.source-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 22px 18px;
  border-top: 1px solid var(--line-soft);
  margin-top: 10px;
}

.conf-label {
  font-size: 11px;
  color: var(--muted);
  flex: none;
}

.conf-bar {
  flex: 1;
}

.conf-value {
  font-family: var(--serif);
  font-size: 15px;
  color: var(--ink);
  flex: none;
  width: 42px;
  text-align: right;
}

.form-body {
  padding: 16px 22px 6px;
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.field-area {
  min-height: 78px;
}

.edited {
  border-color: var(--gold) !important;
  background: #fffdf7;
}

.no-fields {
  font-size: 12.5px;
  color: var(--muted);
  background: #fbf9f4;
  border: 1px dashed var(--line);
  border-radius: 9px;
  padding: 16px;
  text-align: center;
}

.note-field {
  margin-top: 3px;
}

.form-error {
  font-size: 12px;
  color: var(--danger);
  background: var(--danger-soft);
  border: 1px solid #efd0c7;
  border-radius: 7px;
  padding: 9px 12px;
  line-height: 1.6;
}

.changed-count {
  font-family: var(--sans);
  font-size: 10.5px;
  color: var(--gold-deep);
  background: #f7efdc;
  border: 1px solid #e8d8b4;
  border-radius: 4px;
  padding: 2px 6px;
  font-weight: 500;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 22px 22px;
  margin-top: auto;
  border-top: 1px solid var(--line-soft);
}

.form-actions .btn {
  min-width: 118px;
}

@media (max-width: 1000px) {
  .form-card {
    position: static;
  }
}

@media (max-width: 820px) {
  .tab {
    min-width: 100%;
  }
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
