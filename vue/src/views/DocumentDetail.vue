<template>
  <div class="page">
    <div class="page-head detail-head">
      <div class="head-main">
        <router-link to="/documents" class="back-link">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M13 8H3M7 4L3 8l4 4" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          返回文档中心
        </router-link>
        <div class="eyebrow">Document Insight</div>
        <h1 class="page-title">{{ doc ? doc.title : '文档详情' }}</h1>
        <div v-if="doc" class="meta-chips">
          <StatusBadge type="doc" :value="doc.status" />
          <span class="chip">{{ doc.region_label }}</span>
          <span class="chip">{{ doc.doc_type }}</span>
          <span class="chip">{{ doc.version }}</span>
          <span class="chip outline">合规分 {{ doc.compliance_score }}</span>
        </div>
        <div v-if="doc" class="page-sub">
          文件名 {{ doc.filename }} · 生效日期 {{ doc.effective_date || '未标注' }} · {{ doc.pages }} 页 / {{ doc.char_count }} 字
        </div>
      </div>
      <div v-if="doc" class="page-actions">
        <router-link to="/qa" class="btn btn-ghost">前往问答</router-link>
        <button class="btn btn-primary" :disabled="doc.status === 'processing' || rerunning" @click="showRerun = true">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M13 8a5 5 0 11-1.5-3.6M13 2.5V6H9.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          重新运行流水线
        </button>
      </div>
    </div>

    <div v-if="loading" class="card card-pad">
      <SkeletonBlock :lines="7" />
    </div>

    <template v-else-if="doc">
      <section v-if="doc.status === 'processing' || doc.status === 'uploaded'" class="card running-card">
        <div class="running-left">
          <span class="running-spin"></span>
          <div>
            <div class="running-title">Agent 流水线执行中 · {{ doc.current_stage || '等待处理' }}</div>
            <div class="running-sub">页面每 2 秒自动刷新进度，完成后将进入待复核或自动发布。</div>
          </div>
        </div>
        <div class="running-progress">
          <div class="progress gold"><span :style="{ width: doc.progress + '%' }"></span></div>
          <strong>{{ doc.progress }}%</strong>
        </div>
      </section>

      <section v-if="doc.status === 'failed'" class="card failed-card">
        <strong>流水线执行失败</strong>
        <span>{{ doc.summary || '请检查文件内容后重新运行。' }}</span>
      </section>

      <section class="card meta-card">
        <div class="card-head">
          <div class="card-title"><span class="rule"></span>文档元数据</div>
          <span class="card-sub">由元数据补全阶段自动生成，可人工复核</span>
        </div>
        <div class="meta-grid">
          <div class="meta-item"><span>产品名称</span><strong>{{ doc.product_name || '—' }}</strong></div>
          <div class="meta-item"><span>文档类型</span><strong>{{ doc.doc_type }}</strong></div>
          <div class="meta-item"><span>适用地区</span><strong>{{ doc.region_label }}</strong></div>
          <div class="meta-item"><span>条款版本</span><strong>{{ doc.version }}</strong></div>
          <div class="meta-item"><span>生效日期</span><strong>{{ doc.effective_date || '—' }}</strong></div>
          <div class="meta-item"><span>规模</span><strong>{{ doc.pages }} 页 / {{ doc.char_count }} 字</strong></div>
          <div class="meta-item"><span>创建时间</span><strong>{{ doc.created_at }}</strong></div>
          <div class="meta-item"><span>最近更新</span><strong>{{ doc.updated_at }}</strong></div>
        </div>
        <div class="summary-block">
          <div class="summary-label">知识摘要</div>
          <p>{{ doc.summary || '尚未生成摘要' }}</p>
          <div v-if="doc.keywords && doc.keywords.length" class="keyword-row">
            <span v-for="keyword in doc.keywords" :key="keyword" class="chip">{{ keyword }}</span>
          </div>
        </div>
      </section>

      <section class="detail-grid">
        <div class="card timeline-card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>流水线阶段时间线</div>
            <span class="card-sub">{{ completedStages }} / 4 阶段已完成</span>
          </div>
          <div class="timeline">
            <div v-for="item in timeline" :key="item.key" class="timeline-item">
              <div class="timeline-rail">
                <span class="timeline-node" :data-status="item.run ? item.run.status : 'pending'">{{ item.step }}</span>
                <span v-if="item.step < 4" class="timeline-line"></span>
              </div>
              <div class="timeline-body" :class="{ pending: !item.run }">
                <div class="timeline-top">
                  <div>
                    <div class="timeline-name">{{ item.name }}</div>
                    <div class="timeline-desc">{{ item.desc }}</div>
                  </div>
                  <StatusBadge type="run" :value="item.run ? item.run.status : 'pending'" />
                </div>
                <div v-if="item.run" class="timeline-msg">{{ item.run.message }}</div>
                <div v-if="item.run" class="timeline-meta">
                  <span>{{ item.run.finished_at || item.run.started_at }}</span>
                  <span class="sep">·</span>
                  <span>{{ item.run.duration_ms }} ms</span>
                  <span class="sep">·</span>
                  <span>{{ item.run.tokens }} tokens</span>
                </div>
                <div v-else class="timeline-meta">等待执行</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card quality-card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>质检与风险</div>
            <StatusBadge type="risk" :value="doc.risk_level" />
          </div>
          <div class="quality-top">
            <svg viewBox="0 0 120 120" class="gauge">
              <circle cx="60" cy="60" r="46" fill="none" stroke="#F0ECE3" stroke-width="9" />
              <circle
                cx="60"
                cy="60"
                r="46"
                fill="none"
                :stroke="scoreColor"
                stroke-width="9"
                stroke-linecap="round"
                :stroke-dasharray="gauge.dash"
                :stroke-dashoffset="gauge.offset"
                transform="rotate(-90 60 60)"
              />
              <text x="60" y="58" text-anchor="middle" font-size="26" font-family="Georgia, serif" fill="#0F2742">{{ doc.compliance_score }}</text>
              <text x="60" y="76" text-anchor="middle" font-size="9" fill="#8A94A0">合规分 / 100</text>
            </svg>
            <div class="quality-stats">
              <div class="q-row"><span>知识实体</span><strong>{{ doc.entities.length }}</strong></div>
              <div class="q-row"><span>向量切片</span><strong>{{ doc.chunks.total }}</strong></div>
              <div class="q-row"><span>待复核任务</span><strong class="danger">{{ doc.pending_reviews }}</strong></div>
              <div class="q-row"><span>隐式风险</span><strong class="warn">{{ doc.risk_flags.length }}</strong></div>
            </div>
          </div>
          <div class="risk-block">
            <div class="risk-block-head">隐式接口雷达</div>
            <div v-if="doc.risk_flags.length" class="risk-list">
              <div v-for="(flag, index) in doc.risk_flags" :key="index" class="risk-item">
                <StatusBadge type="level" :value="flag.level" size="sm" />
                <div class="risk-copy">
                  <strong>「{{ flag.phrase }}」</strong>
                  <span>{{ flag.section_title }} · {{ flag.object_type }}</span>
                </div>
              </div>
            </div>
            <div v-else class="risk-empty">未发现“按公司规定 / 另行通知 / 最终解释权”等模糊表述。</div>
          </div>
        </div>
      </section>

      <section class="card tabs-card">
        <div class="tabs">
          <button
            class="tab"
            :class="{ active: tab === 'sections' }"
            @click="tab = 'sections'"
          >
            章节结构 <span>{{ doc.sections.length }}</span>
          </button>
          <button
            class="tab"
            :class="{ active: tab === 'entities' }"
            @click="tab = 'entities'"
          >
            知识实体 <span>{{ doc.entities.length }}</span>
          </button>
          <button
            class="tab"
            :class="{ active: tab === 'chunks' }"
            @click="tab = 'chunks'"
          >
            向量切片 <span>{{ doc.chunks.total }}</span>
          </button>
        </div>

        <div v-if="tab === 'sections'" class="tab-body section-list">
          <div v-for="section in doc.sections" :key="section.id" class="section-item">
            <button class="section-head" @click="toggleSection(section.id)">
              <span class="section-no">{{ section.chapter_no || '序' }}</span>
              <div class="section-main">
                <div class="section-title">{{ section.title }}</div>
                <div class="section-meta">第 {{ section.page_start }} 页 · {{ section.content.length }} 字</div>
              </div>
              <svg class="chevron" :class="{ open: isSectionOpen(section.id) }" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 6l4 4 4-4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <div v-if="isSectionOpen(section.id)" class="section-content">{{ section.content }}</div>
          </div>
          <EmptyState v-if="!doc.sections.length" title="暂无章节" desc="重新运行流水线以生成章节结构。" />
        </div>

        <div v-else-if="tab === 'entities'" class="tab-body">
          <div v-for="group in entityGroups" :key="group.type" class="entity-group">
            <button class="group-head" @click="toggleGroup(group.type)">
              <div class="group-left">
                <span class="group-type">{{ group.type }}</span>
                <span class="group-count">{{ group.items.length }} 项</span>
                <span class="group-conf">平均置信度 {{ group.avg }}</span>
              </div>
              <svg class="chevron" :class="{ open: isGroupOpen(group.type) }" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M4 6l4 4 4-4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <div v-if="isGroupOpen(group.type)" class="table-wrap">
              <table class="table entity-table">
                <thead>
                  <tr>
                    <th>对象名称</th>
                    <th style="width: 170px">置信度</th>
                    <th style="width: 90px">状态</th>
                    <th>原文摘录</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="entity in group.items" :key="entity.id">
                    <td>
                      <div class="entity-name">{{ entity.name }}</div>
                      <div class="entity-sub">{{ entity.section_title }}</div>
                    </td>
                    <td>
                      <div class="conf-cell">
                        <div class="progress" :class="entity.confidence < 0.72 ? 'danger' : entity.confidence < 0.8 ? 'gold' : 'success'">
                          <span :style="{ width: entity.confidence * 100 + '%' }"></span>
                        </div>
                        <span>{{ entity.confidence }}</span>
                      </div>
                    </td>
                    <td><StatusBadge type="entity" :value="entity.status" size="sm" /></td>
                    <td><span class="source-text">{{ entity.source_text }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <EmptyState v-if="!doc.entities.length" title="暂无知识实体" desc="流水线尚未生成结构化知识对象。" />
        </div>

        <div v-else class="tab-body chunk-body">
          <div class="chunk-note">
            <span class="chip">HashingEmbedder · 512 维</span>
            <span>字符 2/3-gram 哈希 + L2 归一化，纯本地向量化，无需外部模型。</span>
          </div>
          <div class="chunk-grid">
            <div v-for="chunk in doc.chunks.preview" :key="chunk.id" class="chunk-card">
              <div class="chunk-head">
                <span class="chunk-id">#{{ chunk.id }}</span>
                <span class="chunk-section">{{ chunk.section_title }}</span>
              </div>
              <p class="chunk-content">{{ chunk.content }}</p>
              <div class="chunk-foot">
                <span v-for="keyword in chunk.keywords.slice(0, 4)" :key="keyword" class="chip outline">{{ keyword }}</span>
                <span class="chunk-dim">{{ chunk.embedding_dim }} dim</span>
              </div>
            </div>
          </div>
          <EmptyState v-if="!doc.chunks.preview.length" title="暂无向量切片" desc="重新运行流水线后将生成双轨知识底座。" />
        </div>
      </section>
    </template>

    <ConfirmDialog
      v-if="showRerun"
      title="重新运行流水线"
      message="将清理当前章节、知识实体、向量切片与复核任务，并重新执行 4 阶段抽取。已人工复核的数据会被覆盖，是否继续？"
      confirm-text="确认重新运行"
      :loading="rerunning"
      @cancel="showRerun = false"
      @confirm="rerun"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import api from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { toast } from '../composables/useToast'

const route = useRoute()
const doc = ref(null)
const loading = ref(true)
const tab = ref('sections')
const openSections = ref({})
const openGroups = ref({})
const showRerun = ref(false)
const rerunning = ref(false)
let pollTimer = null

const STAGES = [
  { key: 'section', name: '章节识别', desc: '识别第X章 / 第X条 / 一、/ 1.1 标题并按层级切分' },
  { key: 'metadata', name: '元数据补全', desc: '抽取产品、地区、版本、生效日期与关键词' },
  { key: 'extract', name: '业务内容抽取', desc: '生成 22 类寿险知识对象与向量切片' },
  { key: 'quality', name: '增强与质检', desc: '摘要、合规分、隐式接口雷达与复核分级' }
]

const timeline = computed(() => {
  if (!doc.value) return []
  const runs = doc.value.pipeline_runs || []
  return STAGES.map((stage, index) => ({
    ...stage,
    step: index + 1,
    run: runs.find((run) => run.stage === stage.key)
  }))
})

const completedStages = computed(() =>
  doc.value ? (doc.value.pipeline_runs || []).filter((run) => run.status === 'success').length : 0
)

const entityGroups = computed(() => {
  if (!doc.value) return []
  const map = {}
  for (const entity of doc.value.entities) {
    if (!map[entity.object_type]) map[entity.object_type] = []
    map[entity.object_type].push(entity)
  }
  return Object.entries(map)
    .map(([type, items]) => ({
      type,
      items,
      avg: items.length ? Math.round((items.reduce((sum, item) => sum + item.confidence, 0) / items.length) * 100) / 100 : 0
    }))
    .sort((a, b) => b.items.length - a.items.length)
})

const gauge = computed(() => {
  const circumference = 2 * Math.PI * 46
  const score = doc.value ? doc.value.compliance_score : 0
  return { dash: `${circumference} ${circumference}`, offset: circumference - (score / 100) * circumference }
})

const scoreColor = computed(() => {
  const score = doc.value ? doc.value.compliance_score : 0
  if (score >= 85) return '#1F7A5C'
  if (score >= 70) return '#C7A45C'
  return '#C4553B'
})

function isSectionOpen(id) {
  return openSections.value[id] !== false
}

function toggleSection(id) {
  openSections.value[id] = !isSectionOpen(id)
}

function isGroupOpen(type) {
  return openGroups.value[type] !== false
}

function toggleGroup(type) {
  openGroups.value[type] = !isGroupOpen(type)
}

async function load() {
  try {
    const data = await api.getDocument(route.params.id)
    doc.value = data
    if (!openGroups.value.__init) {
      const groups = {}
      data.entities.forEach((entity, index) => {
        const firstIndex = [...new Set(data.entities.map((item) => item.object_type))].indexOf(entity.object_type)
        groups[entity.object_type] = firstIndex < 4
      })
      openGroups.value = { ...groups, __init: true }
    }
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    loading.value = false
  }
}

async function rerun() {
  rerunning.value = true
  try {
    await api.runDocument(doc.value.id)
    toast('已重新提交流水线')
    showRerun.value = false
    await load()
    startPolling()
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    rerunning.value = false
  }
}

function startPolling() {
  if (pollTimer) window.clearInterval(pollTimer)
  pollTimer = window.setInterval(() => {
    if (!doc.value) return
    if (doc.value.status === 'processing' || doc.value.status === 'uploaded') load()
  }, 2000)
}

onMounted(async () => {
  await load()
  startPolling()
})

onUnmounted(() => {
  if (pollTimer) window.clearInterval(pollTimer)
})
</script>

<style scoped>
.detail-head {
  align-items: flex-start;
}

.head-main {
  min-width: 0;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: var(--muted);
  margin-bottom: 14px;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--gold-deep);
}

.meta-chips {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
  margin-top: 11px;
}

.running-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 22px;
  margin-bottom: 18px;
  border-color: #e8dab7;
  background: #fdf9ef;
}

.running-left {
  display: flex;
  align-items: center;
  gap: 13px;
}

.running-spin {
  width: 21px;
  height: 21px;
  border-radius: 50%;
  border: 2px solid #e2d1a7;
  border-top-color: var(--gold-deep);
  animation: spin 0.9s linear infinite;
  flex: none;
}

.running-title {
  font-family: var(--serif);
  font-size: 14px;
  color: var(--ink);
}

.running-sub {
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}

.running-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 260px;
}

.running-progress .progress {
  flex: 1;
}

.running-progress strong {
  font-family: var(--serif);
  font-size: 18px;
  color: var(--ink);
  min-width: 45px;
}

.failed-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 22px;
  margin-bottom: 18px;
  border-color: #efd0c7;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 13px;
}

.failed-card strong {
  font-family: var(--serif);
}

.meta-card {
  margin-bottom: 18px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  background: var(--line-soft);
  border-top: 1px solid var(--line-soft);
  border-bottom: 1px solid var(--line-soft);
  margin-top: 16px;
}

.meta-item {
  background: #fff;
  padding: 13px 22px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item span {
  font-size: 10.5px;
  color: var(--faint);
}

.meta-item strong {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink);
  font-weight: 600;
  word-break: break-all;
}

.summary-block {
  padding: 17px 22px 20px;
}

.summary-label {
  font-size: 10.5px;
  color: var(--faint);
  margin-bottom: 6px;
  letter-spacing: 0.06em;
}

.summary-block p {
  font-size: 13px;
  color: #3d4b5a;
  line-height: 1.8;
}

.keyword-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
  gap: 18px;
  margin-bottom: 18px;
}

.timeline-card {
  padding-bottom: 12px;
}

.timeline {
  padding: 18px 22px 8px;
}

.timeline-item {
  display: flex;
  gap: 14px;
}

.timeline-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: none;
  width: 30px;
}

.timeline-node {
  width: 27px;
  height: 27px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-family: var(--serif);
  font-size: 11px;
  border: 1px solid var(--line);
  background: #faf8f3;
  color: var(--muted);
}

.timeline-node[data-status='success'] {
  background: var(--ink);
  color: var(--gold-soft);
  border-color: var(--ink);
}

.timeline-node[data-status='running'] {
  background: #faf1dd;
  color: var(--warn);
  border-color: #e6ce9c;
}

.timeline-node[data-status='failed'] {
  background: var(--danger-soft);
  color: var(--danger);
  border-color: #ecc8be;
}

.timeline-line {
  flex: 1;
  width: 1px;
  background: #e9e3d7;
  min-height: 26px;
}

.timeline-body {
  flex: 1;
  padding-bottom: 20px;
  min-width: 0;
}

.timeline-body.pending {
  opacity: 0.6;
}

.timeline-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.timeline-name {
  font-family: var(--serif);
  font-size: 13.5px;
  color: var(--ink);
}

.timeline-desc {
  font-size: 10.5px;
  color: var(--faint);
  margin-top: 1px;
}

.timeline-msg {
  margin-top: 8px;
  font-size: 11.5px;
  color: #46576a;
  background: #faf8f3;
  border-left: 2px solid var(--gold-soft);
  padding: 6px 10px;
  border-radius: 0 5px 5px 0;
  line-height: 1.6;
}

.timeline-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 6px;
  font-size: 10px;
  color: var(--faint);
  flex-wrap: wrap;
}

.sep {
  opacity: 0.6;
}

.quality-card {
  display: flex;
  flex-direction: column;
}

.quality-top {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 22px 8px;
}

.gauge {
  width: 118px;
  height: 118px;
  flex: none;
}

.quality-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.q-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed #f0ece3;
  font-size: 11.5px;
  color: var(--muted);
}

.q-row:last-child {
  border-bottom: 0;
}

.q-row strong {
  font-family: var(--serif);
  font-size: 16px;
  color: var(--ink);
}

.q-row strong.danger {
  color: var(--danger);
}

.q-row strong.warn {
  color: var(--warn);
}

.risk-block {
  margin: 4px 22px 18px;
  border-top: 1px solid var(--line-soft);
  padding-top: 12px;
  flex: 1;
}

.risk-block-head {
  font-size: 10.5px;
  color: var(--faint);
  letter-spacing: 0.06em;
  margin-bottom: 9px;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  background: #fbf9f4;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  padding: 8px 10px;
}

.risk-copy {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.risk-copy strong {
  font-size: 11.5px;
  color: var(--ink);
  font-weight: 600;
}

.risk-copy span {
  font-size: 10px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.risk-empty {
  font-size: 11.5px;
  color: var(--faint);
  line-height: 1.7;
}

.tabs-card {
  overflow: hidden;
}

.tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 0 18px;
  border-bottom: 1px solid var(--line);
  background: #fbf9f4;
  overflow-x: auto;
}

.tab {
  border: 0;
  background: none;
  padding: 14px 15px 12px;
  font-size: 12.5px;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: color 0.15s;
}

.tab span {
  display: inline-grid;
  place-items: center;
  min-width: 18px;
  height: 16px;
  padding: 0 5px;
  border-radius: 8px;
  background: #ece8df;
  color: var(--muted);
  font-size: 9.5px;
  margin-left: 3px;
}

.tab.active {
  color: var(--ink);
  border-bottom-color: var(--gold);
  font-weight: 600;
}

.tab.active span {
  background: var(--ink);
  color: var(--gold-soft);
}

.tab-body {
  padding: 8px 18px 18px;
}

.section-item {
  border-bottom: 1px solid var(--line-soft);
}

.section-item:last-child {
  border-bottom: 0;
}

.section-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 0;
  background: none;
  padding: 13px 6px;
  text-align: left;
}

.section-no {
  min-width: 44px;
  height: 25px;
  border-radius: 5px;
  background: #f5f1e7;
  border: 1px solid #e9e1d0;
  color: #7a6230;
  display: inline-grid;
  place-items: center;
  font-size: 10px;
  padding: 0 6px;
  flex: none;
  max-width: 62px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-main {
  flex: 1;
  min-width: 0;
}

.section-title {
  font-family: var(--serif);
  font-size: 13.5px;
  color: var(--ink);
}

.section-meta {
  font-size: 10px;
  color: var(--faint);
  margin-top: 1px;
}

.chevron {
  color: #aeb6bf;
  flex: none;
  transition: transform 0.18s;
}

.chevron.open {
  transform: rotate(180deg);
}

.section-content {
  white-space: pre-wrap;
  font-size: 12.5px;
  line-height: 1.85;
  color: #405060;
  background: #fbf9f4;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  padding: 13px 15px;
  margin: 0 6px 14px;
}

.entity-group {
  border-bottom: 1px solid var(--line-soft);
}

.entity-group:last-child {
  border-bottom: 0;
}

.group-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 0;
  background: none;
  padding: 13px 6px;
}

.group-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.group-type {
  font-family: var(--serif);
  font-size: 13.5px;
  color: var(--ink);
}

.group-count {
  font-size: 10px;
  color: var(--muted);
  border: 1px solid var(--line);
  background: #faf8f3;
  padding: 1px 7px;
  border-radius: 4px;
}

.group-conf {
  font-size: 10px;
  color: var(--faint);
}

.entity-table {
  margin-bottom: 10px;
}

.entity-name {
  font-size: 12.5px;
  color: var(--ink);
}

.entity-sub {
  font-size: 10px;
  color: var(--faint);
}

.conf-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10.5px;
  color: var(--muted);
  min-width: 130px;
}

.conf-cell .progress {
  width: 90px;
  flex: none;
}

.source-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 11px;
  color: #61707f;
  line-height: 1.65;
}

.chunk-note {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--muted);
  padding: 8px 4px 16px;
}

.chunk-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.chunk-card {
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  background: #fbf9f4;
  padding: 13px 15px;
  display: flex;
  flex-direction: column;
}

.chunk-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.chunk-id {
  font-family: var(--serif);
  font-size: 11px;
  color: var(--gold-deep);
}

.chunk-section {
  font-size: 10.5px;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chunk-content {
  font-size: 11.5px;
  line-height: 1.7;
  color: #4a5a6a;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.chunk-foot {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.chunk-dim {
  margin-left: auto;
  font-size: 9.5px;
  color: var(--faint);
  white-space: nowrap;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1100px) {
  .detail-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .running-card {
    flex-direction: column;
    align-items: stretch;
  }
  .running-progress {
    min-width: 0;
    width: 100%;
  }
}

@media (max-width: 760px) {
  .meta-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .chunk-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .page-actions {
    width: 100%;
  }
}
</style>
