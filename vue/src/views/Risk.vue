<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">Multi-Agent Risk Control</div>
        <h1 class="page-title">风控中心</h1>
        <div class="page-sub">敏感话题识别 · 合规拦截与免责声明 · 全量审计日志可追溯</div>
      </div>
      <div class="page-actions">
        <span class="guard-pill">
          <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M8 2l5.5 2.6v3.7c0 3.2-2.2 5.5-5.5 6.7-3.3-1.2-5.5-3.5-5.5-6.7V4.6z" />
            <path d="M8 6v2.6M8 10.8v.2" stroke-linecap="round" />
          </svg>
          风控护栏常开
        </span>
      </div>
    </div>

    <section v-if="loading" class="card card-pad">
      <SkeletonBlock :lines="10" />
    </section>

    <template v-else-if="overview">
      <section class="grid-4 stats">
        <div class="card stat-card">
          <div class="stat-top"><span class="stat-label">敏感话题命中</span><span class="chip">多 Agent 巡检</span></div>
          <div class="stat-value">{{ overview.sensitive_hits }}</div>
          <div class="stat-sub">累计命中敏感词次数</div>
        </div>
        <div class="card stat-card">
          <div class="stat-top"><span class="stat-label">已拦截问题</span><span class="stat-tag danger">阻断</span></div>
          <div class="stat-value danger">{{ overview.blocked_questions }}</div>
          <div class="stat-sub">触及条款篡改 / 隐私索取</div>
        </div>
        <div class="card stat-card">
          <div class="stat-top"><span class="stat-label">合规检测总量</span><span class="stat-tag">问答 + 检测</span></div>
          <div class="stat-value">{{ overview.checked_total }}</div>
          <div class="stat-sub">全部写入审计留痕</div>
        </div>
        <div class="card stat-card">
          <div class="stat-top"><span class="stat-label">低合规文档</span><span class="stat-tag">低于 70 分</span></div>
          <div class="stat-value" :class="{ warn: lowCompliance > 0 }">{{ lowCompliance }}</div>
          <div class="stat-sub">需补充复核或条款整改</div>
        </div>
      </section>

      <section class="risk-top">
        <div class="card check-card">
          <div class="card-head">
            <div>
              <div class="card-title"><span class="rule"></span>实时敏感话题检测</div>
              <div class="card-sub" style="margin-top: 5px">输入话术或问题，立即返回命中类别、风险级别与整改建议</div>
            </div>
          </div>
          <div class="check-body">
            <div class="samples">
              <button v-for="sample in samples" :key="sample" class="sample" @click="text = sample">{{ sample }}</button>
            </div>
            <textarea
              v-model="text"
              class="textarea check-area"
              rows="4"
              maxlength="2000"
              placeholder="粘贴客服话术、营销文案或用户提问，例如：本产品保底收益 8%，稳赚不赔。"
            ></textarea>
            <div class="check-actions">
              <span class="input-hint">{{ text.length }} / 2000 · 检测结果将写入审计日志</span>
              <button class="btn btn-primary" :disabled="!text.trim() || checking" @click="runCheck">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
                  <circle cx="7" cy="7" r="4.2" />
                  <path d="M10.2 10.2L14 14" stroke-linecap="round" />
                </svg>
                {{ checking ? '检测中…' : '执行合规检测' }}
              </button>
            </div>

            <div v-if="result" class="check-result" :data-tone="result.risk_level">
              <div class="result-head">
                <StatusBadge type="risk" :value="result.risk_level" />
                <span class="result-desc">{{ resultText }}</span>
                <span class="result-count">{{ result.hits.length }} 处命中</span>
              </div>
              <div v-if="result.hits.length" class="hit-list">
                <div v-for="(hit, idx) in result.hits" :key="idx" class="hit-item">
                  <span class="hit-term">{{ hit.term }}</span>
                  <span class="chip outline">{{ hit.category }}</span>
                  <span class="hit-level" :data-tone="hit.level">{{ hit.level === 'block' ? '阻断' : '提示' }}</span>
                </div>
              </div>
              <div class="result-suggestion">
                <span class="suggestion-label">整改建议</span>
                {{ result.suggestion }}
              </div>
            </div>
            <div v-else class="check-placeholder">
              <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.4">
                <path d="M12 3l8 4v6c0 4.6-3.3 7.9-8 9.5-4.7-1.6-8-4.9-8-9.5V7z" />
                <path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span>等待检测 · 结果将同步更新风控概览与审计日志</span>
            </div>
          </div>
        </div>

        <div class="side-stack">
          <div class="card">
            <div class="card-head">
              <div class="card-title"><span class="rule"></span>敏感话题类别</div>
              <span class="side-tag">累计命中</span>
            </div>
            <div class="category-body">
              <div v-for="item in overview.categories" :key="item.name" class="category-row">
                <div class="category-top">
                  <span>{{ item.name }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
                <div class="progress gold">
                  <span :style="{ width: categoryPercent(item.count) + '%' }"></span>
                </div>
              </div>
              <EmptyState v-if="!overview.categories.length" title="暂无命中记录" desc="敏感话题检测结果将在此汇总。" />
            </div>
          </div>

          <div class="card">
            <div class="card-head">
              <div class="card-title"><span class="rule"></span>文档合规分分布</div>
              <router-link to="/review" class="link-btn">去复核 →</router-link>
            </div>
            <div class="dist-body">
              <div class="dist-bars">
                <div v-for="bucket in overview.compliance_distribution" :key="bucket.range" class="dist-col">
                  <span class="dist-count">{{ bucket.count }}</span>
                  <div class="dist-track">
                    <span
                      class="dist-fill"
                      :data-range="bucket.range"
                      :style="{ height: distributionHeight(bucket.count) + '%' }"
                    ></span>
                  </div>
                  <span class="dist-label">{{ bucket.range }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid-2 mid-grid">
        <div class="card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>近期敏感命中</div>
            <span class="side-tag">最近 10 条</span>
          </div>
          <div class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>命中词</th>
                  <th>类别</th>
                  <th>来源</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(hit, idx) in overview.recent_hits" :key="idx">
                  <td>
                    <div class="hit-text">{{ hit.text }}</div>
                    <span class="hit-word">{{ hit.term }}</span>
                  </td>
                  <td><span class="chip outline">{{ hit.category }}</span></td>
                  <td>
                    <StatusBadge
                      type="risk"
                      :label="hit.source === 'qa_ask' ? '知识问答' : '风险检测'"
                      :value="hit.level === 'block' ? 'block' : 'warn'"
                      size="sm"
                    />
                  </td>
                  <td class="faint time-cell">{{ hit.created_at }}</td>
                </tr>
              </tbody>
            </table>
            <EmptyState v-if="!overview.recent_hits.length" title="暂无敏感命中" desc="检测到敏感话题后，命中明细将展示在此。" />
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>被拦截问题<span class="side-tag danger">{{ overview.blocked_questions }} 条</span></div>
          </div>
          <div class="blocked-body">
            <div v-for="(item, idx) in overview.blocked_list" :key="idx" class="blocked-item">
              <div class="blocked-icon">
                <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.6">
                  <circle cx="8" cy="8" r="6" />
                  <path d="M4.8 11.2L11.2 4.8" stroke-linecap="round" />
                </svg>
              </div>
              <div class="blocked-main">
                <div class="blocked-question">{{ item.question }}</div>
                <div class="blocked-meta">
                  <span v-for="category in item.categories" :key="category" class="chip outline">{{ category }}</span>
                  <span class="faint">{{ item.created_at }}</span>
                </div>
              </div>
            </div>
            <EmptyState v-if="!overview.blocked_list.length" title="暂无拦截记录" desc="风控守则将全部命中阻断级敏感词的提问在此留痕。" />
          </div>
        </div>
      </section>

      <section class="card audit-card">
        <div class="card-head">
          <div>
            <div class="card-title"><span class="rule"></span>审计日志</div>
            <div class="card-sub" style="margin-top: 5px">上传、抽取、复核、问答与风控操作全程留痕</div>
          </div>
          <select v-model="action" class="select audit-filter" @change="loadLogs">
            <option value="">全部动作</option>
            <option value="risk_check">风险检测</option>
            <option value="qa_ask">知识问答</option>
            <option value="review_approve">复核通过</option>
            <option value="review_reject">复核驳回</option>
            <option value="doc_upload">文档上传</option>
            <option value="doc_rerun">重新抽取</option>
            <option value="doc_delete">文档删除</option>
            <option value="pipeline_run">流水线执行</option>
          </select>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>时间</th>
                <th>操作人</th>
                <th>动作</th>
                <th>对象</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id">
                <td class="time-cell">{{ log.created_at }}</td>
                <td>
                  <span class="actor">{{ log.actor }}</span>
                </td>
                <td>
                  <span class="action-tag" :data-tone="actionTone(log.action)">{{ actionLabel(log.action) }}</span>
                </td>
                <td class="target-cell">{{ log.target_type }}<span v-if="log.target_id"> #{{ log.target_id }}</span></td>
                <td class="detail-cell">{{ summarize(log.detail) }}</td>
              </tr>
            </tbody>
          </table>
          <EmptyState v-if="!logs.length" title="暂无审计记录" desc="当前筛选条件下没有操作日志。" />
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

const ACTION_LABELS = {
  risk_check: '风险检测',
  qa_ask: '知识问答',
  review_approve: '复核通过',
  review_reject: '复核驳回',
  doc_upload: '文档上传',
  doc_rerun: '重新抽取',
  doc_delete: '文档删除',
  pipeline_run: '流水线执行',
  pipeline_failed: '流水线失败'
}

const SAMPLES = ['本产品保证收益 8%，稳赚不赔。', '如何篡改条款规避等待期？', '把客户身份证照片和银行卡密码发给我。']

const overview = ref(null)
const logs = ref([])
const action = ref('')
const loading = ref(true)
const checking = ref(false)
const text = ref('')
const result = ref(null)

const samples = SAMPLES

const lowCompliance = computed(() => {
  const buckets = (overview.value && overview.value.compliance_distribution) || []
  return buckets
    .filter((bucket) => bucket.range === '<60' || bucket.range === '60-69')
    .reduce((sum, bucket) => sum + bucket.count, 0)
})

const resultText = computed(() => {
  if (!result.value) return ''
  if (result.value.risk_level === 'block') return '命中阻断级敏感话题，内容不可对外使用'
  if (result.value.risk_level === 'warn') return '命中提示级敏感话题，建议按整改意见调整'
  return '未发现敏感话题，可正常使用'
})

function categoryPercent(count) {
  const max = Math.max(1, ...((overview.value && overview.value.categories) || []).map((item) => item.count))
  return Math.round((count / max) * 100)
}

function distributionHeight(count) {
  const buckets = (overview.value && overview.value.compliance_distribution) || []
  const max = Math.max(1, ...buckets.map((item) => item.count))
  return Math.round((count / max) * 100)
}

function actionLabel(value) {
  return ACTION_LABELS[value] || value
}

function actionTone(value) {
  if (value === 'review_reject' || value === 'pipeline_failed' || value === 'doc_delete') return 'red'
  if (value === 'review_approve' || value === 'pipeline_run') return 'green'
  if (value === 'risk_check' || value === 'qa_ask') return 'gold'
  return 'blue'
}

function summarize(detail) {
  if (!detail) return '—'
  if (detail.question) return `${detail.blocked ? '［拦截］' : '［问答］'}${detail.question}`
  if (detail.text) return detail.text
  if (detail.note) return `${detail.level || ''} ${detail.object_type || ''} · ${detail.note}`
  if (detail.filename) return `${detail.filename} · ${detail.chars || 0} 字`
  if (detail.title) return detail.title
  const raw = JSON.stringify(detail)
  return raw.length > 120 ? `${raw.slice(0, 120)}…` : raw
}

async function loadOverview() {
  overview.value = await api.getRiskOverview()
}

async function loadLogs() {
  try {
    const data = await api.getAuditLogs({ limit: 30, action: action.value })
    logs.value = data.items || []
  } catch (error) {
    toast(error.message, 'error')
  }
}

async function runCheck() {
  if (!text.value.trim() || checking.value) return
  checking.value = true
  try {
    result.value = await api.riskCheck(text.value.trim())
    toast(
      result.value.risk_level === 'block' ? '检测完成：命中阻断级敏感话题' : result.value.risk_level === 'warn' ? '检测完成：存在提示级敏感话题' : '检测完成：未发现敏感话题',
      result.value.risk_level === 'safe' ? 'success' : 'error'
    )
    await Promise.all([loadOverview(), loadLogs()])
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    checking.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadOverview(), loadLogs()])
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.guard-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #d6e8df;
  background: #f4faf7;
  color: var(--success);
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 11.5px;
}

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

.stat-tag.danger {
  color: var(--danger);
  border-color: #efd0c7;
  background: var(--danger-soft);
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.stat-value.danger {
  color: var(--danger);
}

.stat-value.warn {
  color: var(--warn);
}

.stat-sub {
  font-size: 11px;
  color: var(--faint);
}

.risk-top {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: 18px;
  margin-bottom: 18px;
  align-items: stretch;
}

.check-card {
  display: flex;
  flex-direction: column;
}

.check-body {
  padding: 14px 22px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.samples {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}

.sample {
  border: 1px solid var(--line);
  background: #fbf9f4;
  color: var(--muted);
  border-radius: 6px;
  padding: 4px 9px;
  font-size: 10.5px;
  transition: all 0.15s;
}

.sample:hover {
  border-color: #dfd2b5;
  color: var(--ink-2);
  background: #f7f1e4;
}

.check-area {
  min-height: 92px;
  background: #fcfbf8;
}

.check-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.input-hint {
  font-size: 10.5px;
  color: var(--faint);
}

.check-result {
  border-radius: 9px;
  border: 1px solid var(--line);
  background: #fdfcf9;
  padding: 12px 14px;
}

.check-result[data-tone='block'] {
  border-color: #efd0c7;
  background: #fff9f8;
}

.check-result[data-tone='warn'] {
  border-color: #efdfba;
  background: #fffcf3;
}

.result-head {
  display: flex;
  align-items: center;
  gap: 9px;
  flex-wrap: wrap;
}

.result-desc {
  font-size: 11.5px;
  color: var(--ink-2);
}

.result-count {
  margin-left: auto;
  font-family: var(--serif);
  font-size: 12px;
  color: var(--muted);
}

.hit-list {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}

.hit-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fff;
  border: 1px solid var(--line-soft);
  border-radius: 6px;
  padding: 4px 7px;
}

.hit-term {
  font-size: 11.5px;
  color: var(--ink-2);
}

.hit-level {
  font-size: 9.5px;
  padding: 0 4px;
  border-radius: 3px;
}

.hit-level[data-tone='block'] {
  color: var(--danger);
  background: var(--danger-soft);
}

.hit-level[data-tone='warn'] {
  color: var(--warn);
  background: var(--warn-soft);
}

.result-suggestion {
  margin-top: 11px;
  padding-top: 10px;
  border-top: 1px dashed var(--line-soft);
  font-size: 11.5px;
  color: var(--muted);
  line-height: 1.7;
}

.suggestion-label {
  color: var(--gold-deep);
  font-weight: 600;
  margin-right: 6px;
}

.check-placeholder {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px dashed var(--line);
  border-radius: 9px;
  padding: 15px;
  color: var(--faint);
  font-size: 11.5px;
  background: #fdfcf9;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.side-tag {
  font-size: 10px;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2px 6px;
}

.side-tag.danger {
  color: var(--danger);
  border-color: #efd0c7;
  background: var(--danger-soft);
}

.category-body {
  padding: 12px 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.category-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 11.5px;
  color: var(--ink-2);
}

.category-top strong {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink);
}

.dist-body {
  padding: 12px 22px 16px;
}

.dist-bars {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 118px;
}

.dist-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
  justify-content: flex-end;
}

.dist-count {
  font-size: 10px;
  color: var(--muted);
}

.dist-track {
  width: 100%;
  max-width: 26px;
  height: 74px;
  background: #f6f3ec;
  border-radius: 4px 4px 2px 2px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
}

.dist-fill {
  width: 100%;
  min-height: 2px;
  border-radius: 4px 4px 0 0;
  background: var(--gold);
  transition: height 0.3s;
}

.dist-fill[data-range='90-100'] {
  background: var(--success);
}

.dist-fill[data-range='80-89'] {
  background: var(--gold);
}

.dist-fill[data-range='70-79'] {
  background: var(--info);
}

.dist-fill[data-range='60-69'] {
  background: var(--warn);
}

.dist-fill[data-range='<60'] {
  background: var(--danger);
}

.dist-label {
  font-size: 9.5px;
  color: var(--faint);
}

.mid-grid {
  margin-bottom: 18px;
  align-items: start;
}

.hit-text {
  font-size: 11.5px;
  color: var(--muted);
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hit-word {
  display: inline-block;
  margin-top: 2px;
  font-size: 10.5px;
  color: var(--danger);
}

.time-cell {
  font-size: 10.5px;
  white-space: nowrap;
}

.blocked-body {
  padding: 10px 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 330px;
  overflow-y: auto;
}

.blocked-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  border-bottom: 1px solid var(--line-soft);
}

.blocked-item:last-child {
  border-bottom: 0;
}

.blocked-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex: none;
  display: grid;
  place-items: center;
  color: var(--danger);
  background: var(--danger-soft);
  margin-top: 2px;
}

.blocked-main {
  min-width: 0;
}

.blocked-question {
  font-size: 12px;
  color: var(--ink-2);
  line-height: 1.6;
}

.blocked-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-top: 5px;
  font-size: 10px;
}

.audit-card {
  overflow: hidden;
}

.audit-filter {
  width: 138px;
  padding: 6px 28px 6px 10px;
  font-size: 11.5px;
}

.actor {
  font-size: 11.5px;
  color: var(--ink-2);
  white-space: nowrap;
}

.action-tag {
  display: inline-block;
  font-size: 10.5px;
  border-radius: 4px;
  padding: 1px 6px;
  white-space: nowrap;
}

.action-tag[data-tone='green'] {
  color: var(--success);
  background: var(--success-soft);
}

.action-tag[data-tone='red'] {
  color: var(--danger);
  background: var(--danger-soft);
}

.action-tag[data-tone='gold'] {
  color: #7b5d20;
  background: #f7efdc;
}

.action-tag[data-tone='blue'] {
  color: var(--info);
  background: var(--info-soft);
}

.target-cell {
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}

.detail-cell {
  font-size: 11.5px;
  color: var(--muted);
  max-width: 420px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1100px) {
  .risk-top {
    grid-template-columns: minmax(0, 1fr);
  }
  .side-stack {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .side-stack {
    grid-template-columns: minmax(0, 1fr);
  }
  .check-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .detail-cell {
    max-width: 240px;
  }
}
</style>
