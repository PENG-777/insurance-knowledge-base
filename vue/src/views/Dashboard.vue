<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">Operations Overview</div>
        <h1 class="page-title">知识资产概览</h1>
        <div class="page-sub">4 阶段 Agent 抽取流水线 · 双轨知识底座 · 人机协同质量治理</div>
      </div>
      <div class="page-actions">
        <router-link to="/qa" class="btn btn-ghost">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M3 4h10v6H7l-4 3z" />
          </svg>
          知识问答
        </router-link>
        <router-link to="/documents" class="btn btn-primary">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M8 3v10M3 8h10" stroke-linecap="round" />
          </svg>
          上传文档
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="grid-4">
      <div v-for="n in 4" :key="n" class="card card-pad">
        <SkeletonBlock :lines="3" />
      </div>
    </div>

    <template v-else-if="data">
      <section class="grid-4 kpi-grid">
        <div v-for="item in kpis" :key="item.label" class="card kpi-card">
          <div class="kpi-top">
            <span class="kpi-icon" :data-tone="item.tone">
              <svg viewBox="0 0 20 20" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" v-html="item.icon"></svg>
            </span>
            <span class="kpi-trend" :data-tone="item.tone">{{ item.tag }}</span>
          </div>
          <div class="stat-value">{{ item.value }}</div>
          <div class="kpi-foot">
            <span class="stat-label">{{ item.label }}</span>
            <span class="kpi-sub">{{ item.sub }}</span>
          </div>
        </div>
      </section>

      <section class="card pipeline-card">
        <div class="card-head">
          <div>
            <div class="card-title"><span class="rule"></span>四阶段 Agent 抽取流水线</div>
            <div class="card-sub" style="margin-top: 5px">章节识别 → 元数据补全 → 业务内容抽取 → 增强与质检</div>
          </div>
          <span class="runtime-tag">
            <span class="pulse-dot"></span>
            {{ data.kpis.processing }} 份文档待处理 / 处理中
          </span>
        </div>
        <div class="pipeline">
          <div v-for="(stage, index) in data.stage_distribution" :key="stage.stage" class="stage">
            <div class="stage-node">
              <span class="stage-no">{{ index + 1 }}</span>
              <div class="stage-body">
                <div class="stage-name">{{ stage.name }}</div>
                <div class="stage-meta">{{ stage.count }} 份文档 · 均耗时 {{ formatMs(stage.avg_duration_ms) }}</div>
              </div>
            </div>
            <div v-if="index < data.stage_distribution.length - 1" class="connector">
              <span></span>
            </div>
          </div>
        </div>
      </section>

      <section class="grid-2 charts">
        <div class="card trend-card">
          <div class="card-head">
            <div>
              <div class="card-title"><span class="rule"></span>合规趋势</div>
              <div class="card-sub" style="margin-top: 5px">近 7 日知识入库与平均合规分</div>
            </div>
            <div class="legend">
              <span><i class="legend-line"></i>合规分</span>
              <span><i class="legend-bar"></i>文档数</span>
            </div>
          </div>
          <div class="chart-body">
            <svg viewBox="0 0 620 232" preserveAspectRatio="xMidYMid meet" role="img" aria-label="近7日合规趋势">
              <line
                v-for="grid in chart.gridLines"
                :key="grid.value"
                x1="40"
                :y1="grid.y"
                x2="604"
                :y2="grid.y"
                stroke="#EFEADF"
                stroke-width="1"
              />
              <text
                v-for="grid in chart.gridLines"
                :key="'t' + grid.value"
                x="32"
                :y="grid.y + 3"
                text-anchor="end"
                fill="#9AA3AD"
                font-size="9"
              >{{ grid.value }}</text>
              <rect
                v-for="bar in chart.bars"
                :key="'b' + bar.date"
                :x="bar.x"
                :y="bar.y"
                :width="bar.width"
                :height="bar.height"
                rx="2"
                fill="rgba(15, 39, 66, 0.1)"
              />
              <polygon :points="chart.area" fill="rgba(199, 164, 92, 0.13)" />
              <polyline
                :points="chart.line"
                fill="none"
                stroke="#C7A45C"
                stroke-width="2"
                stroke-linejoin="round"
              />
              <g v-for="point in chart.points" :key="point.date">
                <circle :cx="point.x" :cy="point.y" r="4.2" fill="#fff" stroke="#C7A45C" stroke-width="1.6" />
                <text :x="point.x" :y="216" text-anchor="middle" fill="#7C8792" font-size="10">{{ point.date }}</text>
                <text
                  :x="point.x"
                  :y="point.y - 10"
                  text-anchor="middle"
                  fill="#8A6B2C"
                  font-size="9.5"
                  font-weight="600"
                >{{ point.compliance }}</text>
              </g>
            </svg>
          </div>
        </div>

        <div class="card review-card">
          <div class="card-head">
            <div>
              <div class="card-title"><span class="rule"></span>复核级别分布</div>
              <div class="card-sub" style="margin-top: 5px">P0 紧急 · P1 重要 · P2 建议</div>
            </div>
            <router-link to="/review" class="link-btn">进入工作台 →</router-link>
          </div>
          <div class="donut-wrap">
            <svg viewBox="0 0 168 168" class="donut" role="img" aria-label="复核级别分布">
              <circle cx="84" cy="84" r="58" fill="none" stroke="#F1ECE2" stroke-width="16" />
              <g transform="rotate(-90 84 84)">
                <circle
                  v-for="seg in donut.segments"
                  :key="seg.level"
                  cx="84"
                  cy="84"
                  r="58"
                  fill="none"
                  :stroke="seg.color"
                  stroke-width="16"
                  :stroke-dasharray="seg.dash"
                  :stroke-dashoffset="seg.offset"
                  stroke-linecap="butt"
                />
              </g>
              <text x="84" y="80" text-anchor="middle" fill="#0F2742" font-size="27" font-family="Georgia, serif">{{ donut.total }}</text>
              <text x="84" y="100" text-anchor="middle" fill="#8A94A0" font-size="10">待复核任务</text>
            </svg>
            <div class="donut-legend">
              <div v-for="seg in donut.segments" :key="seg.level" class="donut-item">
                <span class="donut-dot" :style="{ background: seg.color }"></span>
                <div class="donut-name">
                  <strong>{{ seg.level }}</strong>
                  <span>{{ seg.label }}</span>
                </div>
                <div class="donut-count">{{ seg.count }}</div>
              </div>
              <div class="donut-tip">
                当前待复核 {{ donut.total }} 项，其中 P0 占比 {{ donut.p0Ratio }}%
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid-2 bottom-grid">
        <div class="card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>最新文档</div>
            <router-link to="/documents" class="link-btn">查看全部 →</router-link>
          </div>
          <div class="doc-list">
            <router-link
              v-for="doc in data.latest_documents"
              :key="doc.id"
              :to="`/documents/${doc.id}`"
              class="doc-row"
            >
              <div class="doc-lockup">
                <span class="doc-region">{{ doc.region_label }}</span>
                <div class="doc-main">
                  <div class="doc-title">{{ doc.title }}</div>
                  <div class="doc-meta">{{ doc.doc_type }} · {{ doc.version }} · {{ doc.char_count }} 字</div>
                </div>
              </div>
              <div class="doc-right">
                <StatusBadge type="doc" :value="doc.status" size="sm" />
                <span class="score">{{ doc.compliance_score || '—' }}<small>分</small></span>
              </div>
            </router-link>
            <EmptyState v-if="!data.latest_documents.length" title="暂无文档" desc="上传首份条款文件后，流水线将自动完成知识抽取。" />
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <span class="rule"></span>待复核队列
              <span class="queue-count">{{ data.kpis.pending_reviews }}</span>
            </div>
            <router-link to="/review" class="link-btn">全部任务 →</router-link>
          </div>
          <div class="queue-list">
            <router-link
              v-for="task in data.review_queue"
              :key="task.id"
              to="/review"
              class="queue-row"
            >
              <StatusBadge type="level" :value="task.level" size="sm" />
              <div class="queue-main">
                <div class="queue-title">{{ task.object_type }} · {{ task.document_title }}</div>
                <div class="queue-reason">{{ task.trigger_reason }}</div>
              </div>
              <svg class="queue-arrow" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M3 8h10M9 4l4 4-4 4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </router-link>
            <EmptyState v-if="!data.review_queue.length" title="复核队列已清空" desc="当前没有 P0/P1/P2 待处理任务。" />
          </div>
        </div>
      </section>

      <section class="card status-strip">
        <div class="status-strip-head">文档状态分布</div>
        <div class="status-bars">
          <div v-for="item in data.status_distribution" :key="item.key" class="status-bar">
            <div class="status-bar-top">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
            <div class="progress" :class="statusTone(item.key)">
              <span :style="{ width: statusPercent(item.count) + '%' }"></span>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import api from '../api'
import EmptyState from '../components/EmptyState.vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { toast } from '../composables/useToast'

const data = ref(null)
const loading = ref(true)

const kpis = computed(() => {
  if (!data.value) return []
  const { kpis: k, review_levels: levels } = data.value
  return [
    {
      label: '文档资产',
      value: k.documents,
      sub: `已发布 ${k.published} 份`,
      tag: '知识入库',
      tone: 'gold',
      icon: '<path d="M5 2.8h6.5L16 7.3v9.9H5z"/><path d="M11 3v4.4h4.6" />'
    },
    {
      label: '知识对象',
      value: k.entities,
      sub: '覆盖 22 类寿险对象',
      tag: '结构化',
      tone: 'blue',
      icon: '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="11" y="3" width="6" height="6" rx="1"/><rect x="3" y="11" width="6" height="6" rx="1"/><rect x="11" y="11" width="6" height="6" rx="1"/>'
    },
    {
      label: '待复核任务',
      value: k.pending_reviews,
      sub: `P0 紧急 ${levels.P0 || 0} 项`,
      tag: '人机协同',
      tone: 'amber',
      icon: '<path d="M10 2.6l7 3v5.1c0 4.2-2.9 7.1-7 8.7-4.1-1.6-7-4.5-7-8.7V5.6z"/><path d="M10 7v4M10 13.6v.2"/>'
    },
    {
      label: '平均合规分',
      value: k.compliance_rate,
      sub: '发布阈值 85 分',
      tag: '质量治理',
      tone: 'green',
      icon: '<path d="M3 16V9M8 16V5M13 16v-4M18 16V7"/><path d="M2 17.5h17"/>'
    }
  ]
})

const chart = computed(() => {
  const trend = (data.value && data.value.trend) || []
  const left = 40
  const right = 604
  const top = 20
  const bottom = 192
  const innerH = bottom - top
  const step = trend.length > 1 ? (right - left) / (trend.length - 1) : 0
  const min = 50
  const max = 100
  const points = trend.map((item, index) => {
    const ratio = Math.max(0, Math.min(1, (item.compliance - min) / (max - min)))
    return {
      ...item,
      x: left + step * index,
      y: bottom - ratio * innerH
    }
  })
  const line = points.map((p) => `${p.x},${p.y}`).join(' ')
  const area = points.length ? `${left},${bottom} ${line} ${right},${bottom}` : ''
  const bars = points.map((p) => {
    const height = Math.min(innerH * 0.5, p.documents * 22)
    return { date: p.date, x: p.x - 13, y: bottom - height, width: 26, height }
  })
  const gridLines = [50, 60, 70, 80, 90, 100].map((value) => ({
    value,
    y: bottom - ((value - min) / (max - min)) * innerH
  }))
  return { points, line, area, bars, gridLines }
})

const donut = computed(() => {
  const levels = (data.value && data.value.review_levels) || {}
  const list = [
    { level: 'P0', label: '紧急复核', count: levels.P0 || 0, color: '#C4553B' },
    { level: 'P1', label: '重要复核', count: levels.P1 || 0, color: '#C7A45C' },
    { level: 'P2', label: '建议优化', count: levels.P2 || 0, color: '#2D5C86' }
  ]
  const total = list.reduce((sum, item) => sum + item.count, 0)
  const circumference = 2 * Math.PI * 58
  let cursor = 0
  const segments = list.map((item) => {
    const ratio = total ? item.count / total : 0
    const dash = `${ratio * circumference} ${circumference}`
    const offset = -cursor * circumference
    cursor += ratio
    return { ...item, dash, offset }
  })
  const p0Ratio = total ? Math.round((list[0].count / total) * 100) : 0
  return { segments, total, p0Ratio }
})

function formatMs(ms) {
  if (!ms) return '0 ms'
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

function statusPercent(count) {
  const total = (data.value && data.value.kpis.documents) || 0
  return total ? Math.round((count / total) * 100) : 0
}

function statusTone(key) {
  return { published: 'success', review: 'gold', processing: '', failed: 'danger' }[key] || ''
}

async function load() {
  loading.value = true
  try {
    data.value = await api.getDashboard()
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.kpi-grid {
  margin-bottom: 18px;
}

.kpi-card {
  padding: 18px 20px;
  min-height: 128px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 13px;
}

.kpi-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--ink-2);
  background: #f4f2ec;
  border: 1px solid var(--line);
}

.kpi-icon[data-tone='gold'] {
  color: #8a6b2c;
  background: #faf3e2;
  border-color: #eadcbb;
}

.kpi-icon[data-tone='blue'] {
  color: var(--info);
  background: var(--info-soft);
  border-color: #dbe6f0;
}

.kpi-icon[data-tone='amber'] {
  color: var(--warn);
  background: var(--warn-soft);
  border-color: #eee0c1;
}

.kpi-icon[data-tone='green'] {
  color: var(--success);
  background: var(--success-soft);
  border-color: #d6e8df;
}

.kpi-trend {
  font-size: 10px;
  letter-spacing: 0.04em;
  color: var(--muted);
  border: 1px solid var(--line);
  padding: 2px 7px;
  border-radius: 4px;
  background: #fbf9f4;
}

.kpi-trend[data-tone='amber'] {
  color: var(--warn);
  border-color: #eee0c1;
  background: #fdf8ee;
}

.kpi-trend[data-tone='green'] {
  color: var(--success);
  border-color: #d6e8df;
  background: #f4faf7;
}

.kpi-foot {
  margin-top: auto;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.kpi-sub {
  font-size: 11px;
  color: var(--faint);
  white-space: nowrap;
}

.pipeline-card {
  margin-bottom: 18px;
  overflow: hidden;
}

.pipeline {
  display: flex;
  align-items: stretch;
  padding: 22px 22px 24px;
  gap: 0;
}

.stage {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.stage-node {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  background: #fbfaf6;
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 13px 14px;
}

.stage-no {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  flex: none;
  display: grid;
  place-items: center;
  background: var(--ink);
  color: var(--gold-soft);
  font-family: var(--serif);
  font-size: 12px;
  border: 1px solid rgba(199, 164, 92, 0.35);
}

.stage-body {
  min-width: 0;
}

.stage-name {
  font-family: var(--serif);
  font-size: 13.5px;
  color: var(--ink);
  white-space: nowrap;
}

.stage-meta {
  font-size: 10.5px;
  color: var(--muted);
  margin-top: 2px;
  white-space: nowrap;
}

.connector {
  flex: 0 0 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #d5c69f;
}

.connector span {
  width: 16px;
  height: 1px;
  background: #ddcfad;
  position: relative;
}

.connector span::after {
  content: "";
  position: absolute;
  right: -1px;
  top: -2.5px;
  border-left: 4px solid #ddcfad;
  border-top: 3px solid transparent;
  border-bottom: 3px solid transparent;
}

.runtime-tag {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  color: var(--muted);
  background: #fbf9f4;
  border: 1px solid var(--line);
  padding: 4px 9px;
  border-radius: 6px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  box-shadow: 0 0 0 3px rgba(199, 164, 92, 0.16);
}

.charts {
  margin-bottom: 18px;
}

.trend-card,
.review-card {
  min-height: 330px;
}

.legend {
  display: flex;
  gap: 12px;
  font-size: 10.5px;
  color: var(--muted);
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-line {
  width: 14px;
  height: 2px;
  background: var(--gold);
  display: inline-block;
}

.legend-bar {
  width: 9px;
  height: 9px;
  background: rgba(15, 39, 66, 0.12);
  display: inline-block;
  border-radius: 2px;
}

.chart-body {
  padding: 4px 12px 6px;
}

.chart-body svg {
  width: 100%;
  height: auto;
}

.donut-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px 26px;
}

.donut {
  width: 168px;
  height: 168px;
  flex: none;
}

.donut-legend {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.donut-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px 0;
  border-bottom: 1px dashed #f0ece3;
}

.donut-item:last-of-type {
  border-bottom: 0;
}

.donut-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex: none;
}

.donut-name {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.donut-name strong {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink);
}

.donut-name span {
  font-size: 10.5px;
  color: var(--muted);
}

.donut-count {
  font-family: var(--serif);
  font-size: 19px;
  color: var(--ink);
}

.donut-tip {
  font-size: 10.5px;
  color: var(--faint);
  line-height: 1.6;
  margin-top: 4px;
  padding-top: 10px;
  border-top: 1px solid var(--line-soft);
}

.bottom-grid {
  margin-bottom: 18px;
}

.doc-list,
.queue-list {
  padding: 8px 10px 12px;
}

.doc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 11px 12px;
  border-radius: 9px;
  transition: background 0.15s;
  border-bottom: 1px solid var(--line-soft);
}

.doc-row:last-child {
  border-bottom: 0;
}

.doc-row:hover {
  background: #fbf8f1;
}

.doc-lockup {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.doc-region {
  width: 34px;
  height: 34px;
  border-radius: 7px;
  background: #f4f0e5;
  border: 1px solid #e8dfca;
  color: #7a6230;
  display: grid;
  place-items: center;
  font-size: 10.5px;
  font-weight: 600;
  flex: none;
}

.doc-main {
  min-width: 0;
}

.doc-title {
  font-family: var(--serif);
  font-size: 13.5px;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  font-size: 10.5px;
  color: var(--muted);
  margin-top: 2px;
}

.doc-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: none;
}

.score {
  font-family: var(--serif);
  font-size: 16px;
  color: var(--ink);
  min-width: 38px;
  text-align: right;
}

.score small {
  font-family: var(--sans);
  font-size: 9px;
  color: var(--faint);
  margin-left: 2px;
}

.queue-count {
  min-width: 20px;
  height: 18px;
  border-radius: 9px;
  padding: 0 6px;
  background: var(--danger-soft);
  color: var(--danger);
  font-family: var(--sans);
  font-size: 10.5px;
  display: inline-grid;
  place-items: center;
}

.queue-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 11px 12px;
  border-radius: 9px;
  transition: background 0.15s;
  border-bottom: 1px solid var(--line-soft);
}

.queue-row:last-child {
  border-bottom: 0;
}

.queue-row:hover {
  background: #fbf8f1;
}

.queue-main {
  flex: 1;
  min-width: 0;
}

.queue-title {
  font-size: 12.5px;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-reason {
  font-size: 10.5px;
  color: var(--muted);
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-arrow {
  color: #b9c0c8;
  margin-top: 4px;
  flex: none;
}

.status-strip {
  padding: 18px 22px 20px;
}

.status-strip-head {
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
  margin-bottom: 15px;
}

.status-bars {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 18px;
}

.status-bar-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 11.5px;
  color: var(--muted);
  margin-bottom: 6px;
}

.status-bar-top strong {
  font-family: var(--serif);
  color: var(--ink);
  font-size: 16px;
}

@media (max-width: 1100px) {
  .pipeline {
    flex-wrap: wrap;
    gap: 12px;
  }
  .stage {
    flex: 1 1 45%;
  }
  .connector {
    display: none;
  }
}

@media (max-width: 820px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .pipeline {
    flex-direction: column;
  }
  .stage {
    width: 100%;
  }
  .stage-node {
    width: 100%;
  }
  .donut-wrap {
    flex-direction: column;
  }
  .status-bars {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .kpi-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
