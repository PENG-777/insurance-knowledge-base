<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">Document Intelligence</div>
        <h1 class="page-title">文档中心</h1>
        <div class="page-sub">上传保单条款，Agent 自动完成章节切分、元数据补全、知识抽取与质检</div>
      </div>
      <div class="page-actions">
        <button class="btn btn-ghost" :disabled="loading" @click="load">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M13 8a5 5 0 11-1.5-3.6M13 2.5V6H9.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          刷新列表
        </button>
        <button class="btn btn-primary" @click="triggerUpload">
          <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M8 10V2.5M5 5l3-3 3 3M2.8 10v2.7h10.4V10" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          上传文档
        </button>
      </div>
    </div>

    <input ref="fileInput" type="file" accept=".pdf,.txt,.md" hidden @change="onFileChange" />

    <section
      class="upload-card"
      :class="{ dragging: dragActive, busy: uploadState.active }"
      @click="triggerUpload"
      @dragover.prevent="dragActive = true"
      @dragleave.prevent="dragActive = false"
      @drop.prevent="onDrop"
    >
      <div class="upload-inner">
        <div class="upload-icon">
          <svg viewBox="0 0 32 32" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.4">
            <path d="M16 21V7M10.5 12.5L16 7l5.5 5.5" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M6 21v5h20v-5" stroke-linecap="round" />
          </svg>
        </div>
        <div class="upload-copy">
          <div class="upload-title">{{ uploadState.active ? '正在上传并启动 Agent 流水线' : '拖拽条款文件至此，或点击选择文件' }}</div>
          <div class="upload-sub">
            支持 PDF / TXT / Markdown · 单文件建议不超过 20 MB · 上传后自动进入 4 阶段抽取
          </div>
          <div v-if="uploadState.active" class="upload-progress">
            <div class="upload-file">{{ uploadState.name }}</div>
            <div class="progress gold">
              <span :style="{ width: uploadState.progress + '%' }"></span>
            </div>
            <span class="upload-percent">{{ uploadState.progress }}%</span>
          </div>
        </div>
        <div class="upload-side">
          <span class="chip outline">加密传输</span>
          <span class="chip">演示数据不涉真实客户</span>
        </div>
      </div>
    </section>

    <section class="card filter-card">
      <div class="filter-grid">
        <div class="field">
          <label class="field-label">状态</label>
          <select v-model="filters.status" class="select" @change="applyFilters">
            <option value="">全部状态</option>
            <option value="uploaded">待处理</option>
            <option value="processing">处理中</option>
            <option value="review">待复核</option>
            <option value="published">已发布</option>
            <option value="failed">失败</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">地区</label>
          <select v-model="filters.region" class="select" @change="applyFilters">
            <option value="">全部地区</option>
            <option value="HK">香港</option>
            <option value="MO">澳门</option>
            <option value="OVERSEAS">海外</option>
            <option value="CN">内地</option>
          </select>
        </div>
        <div class="field filter-search">
          <label class="field-label">关键词</label>
          <div class="search-box">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="7" cy="7" r="4.5" />
              <path d="M10.5 10.5L14 14" stroke-linecap="round" />
            </svg>
            <input
              v-model="filters.keyword"
              class="input"
              placeholder="搜索文档标题、产品名或摘要"
              @keyup.enter="applyFilters"
            />
          </div>
        </div>
        <div class="filter-actions">
          <button class="btn btn-ghost" @click="resetFilters">重置</button>
          <button class="btn btn-primary" @click="applyFilters">查询</button>
        </div>
      </div>
      <div class="filter-summary">
        <span>共 <strong>{{ total }}</strong> 份文档</span>
        <span v-if="processingDoc" class="running">
          <span class="spin"></span>
          {{ processingDoc.title }} · {{ processingDoc.current_stage }} {{ processingDoc.progress }}%
        </span>
      </div>
    </section>

    <section class="card table-card">
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>文档</th>
              <th>类型 / 版本</th>
              <th>状态</th>
              <th>流水线进度</th>
              <th>合规分</th>
              <th>待复核</th>
              <th>更新时间</th>
              <th class="right">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="n in 5" :key="'sk' + n">
                <td colspan="8"><SkeletonBlock :lines="1" height="18px" /></td>
              </tr>
            </template>
            <tr v-for="doc in items" v-else :key="doc.id">
              <td>
                <div class="doc-cell">
                  <span class="file-mark" :data-region="doc.region">
                    <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.3">
                      <path d="M5 2.6h6.2L15 6.4v11H5z" />
                      <path d="M11 3v4h4" />
                    </svg>
                  </span>
                  <div class="doc-copy">
                    <router-link :to="`/documents/${doc.id}`" class="doc-name">{{ doc.title }}</router-link>
                    <span class="doc-file">
                      {{ doc.filename }} · {{ doc.region_label }} · {{ doc.char_count }} 字
                    </span>
                  </div>
                </div>
              </td>
              <td>
                <div>{{ doc.doc_type }}</div>
                <div class="tiny">{{ doc.version }} · {{ doc.effective_date || '未标注生效日' }}</div>
              </td>
              <td><StatusBadge type="doc" :value="doc.status" /></td>
              <td>
                <div class="progress-cell">
                  <div class="progress" :class="doc.status === 'failed' ? 'danger' : doc.status === 'published' ? 'success' : 'gold'">
                    <span :style="{ width: Math.max(doc.progress, doc.status === 'published' ? 100 : 2) + '%' }"></span>
                  </div>
                  <span class="progress-text">
                    {{ doc.status === 'published' ? '已完成' : (doc.current_stage || '等待处理') }} {{ doc.progress }}%
                  </span>
                </div>
              </td>
              <td>
                <div class="score-cell">
                  <strong>{{ doc.compliance_score || '—' }}</strong>
                  <span class="score-bar">
                    <span
                      :style="{ width: doc.compliance_score + '%' }"
                      :class="{ low: doc.compliance_score && doc.compliance_score < 70 }"
                      :data-risk="doc.risk_level"
                    ></span>
                  </span>
                </div>
              </td>
              <td>
                <span v-if="doc.pending_reviews" class="review-pill">{{ doc.pending_reviews }}</span>
                <span v-else class="faint">—</span>
              </td>
              <td class="tiny">{{ doc.updated_at }}</td>
              <td class="right">
                <div class="row-actions">
                  <router-link :to="`/documents/${doc.id}`" class="link-btn">查看</router-link>
                  <button class="link-btn" :disabled="doc.status === 'processing'" @click="rerun(doc)">重新运行</button>
                  <button class="link-btn danger" @click="askDelete(doc)">删除</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && !items.length">
              <td colspan="8">
                <EmptyState title="暂无匹配文档" desc="调整筛选条件，或拖拽一份新的条款文件开始抽取。">
                  <button class="btn btn-ghost" @click="resetFilters">清空筛选</button>
                </EmptyState>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="pages > 0" class="pager">
        <span class="pager-info">第 {{ page }} / {{ pages }} 页 · 每页 {{ pageSize }} 条</span>
        <div class="pager-actions">
          <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
          <button class="btn btn-ghost btn-sm" :disabled="page >= pages" @click="goPage(page + 1)">下一页</button>
        </div>
      </div>
    </section>

    <ConfirmDialog
      v-if="deleteTarget"
      title="删除文档"
      :message="`确认删除《${deleteTarget.title}》？章节、实体、向量切片与复核任务将一并清除，操作不可撤销。`"
      confirm-text="确认删除"
      danger
      :loading="deleting"
      @cancel="deleteTarget = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import api from '../api'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import SkeletonBlock from '../components/SkeletonBlock.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { toast } from '../composables/useToast'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pages = ref(0)
const pageSize = 8
const loading = ref(true)
const fileInput = ref(null)
const dragActive = ref(false)
const deleting = ref(false)
const deleteTarget = ref(null)
const uploadState = reactive({ active: false, name: '', progress: 0 })

const filters = reactive({ status: '', region: '', keyword: '' })
let pollTimer = null

const processingDoc = computed(() =>
  items.value.find((doc) => doc.status === 'processing' || doc.status === 'uploaded')
)

function triggerUpload() {
  if (uploadState.active) return
  fileInput.value && fileInput.value.click()
}

function onFileChange(event) {
  const files = event.target.files
  if (files && files.length) uploadFile(files[0])
  event.target.value = ''
}

function onDrop(event) {
  dragActive.value = false
  const files = event.dataTransfer.files
  if (files && files.length) uploadFile(files[0])
}

async function uploadFile(file) {
  if (!/\.(pdf|txt|md)$/i.test(file.name)) {
    toast('仅支持 PDF、TXT、Markdown 文件', 'error')
    return
  }
  const form = new FormData()
  form.append('file', file)
  uploadState.active = true
  uploadState.name = file.name
  uploadState.progress = 0
  try {
    await api.uploadDocument(form, (event) => {
      if (event.total) uploadState.progress = Math.round((event.loaded / event.total) * 100)
    })
    uploadState.progress = 100
    toast('文件已上传，Agent 流水线开始执行')
    await load()
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    window.setTimeout(() => {
      uploadState.active = false
      uploadState.progress = 0
      uploadState.name = ''
    }, 800)
  }
}

async function load() {
  loading.value = true
  try {
    const data = await api.getDocuments({
      status: filters.status,
      region: filters.region,
      keyword: filters.keyword,
      page: page.value,
      pageSize
    })
    items.value = data.items
    total.value = data.total
    pages.value = data.pages
    if (page.value > data.pages && data.pages > 0) {
      page.value = data.pages
      await load()
    }
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  load()
}

function resetFilters() {
  filters.status = ''
  filters.region = ''
  filters.keyword = ''
  page.value = 1
  load()
}

function goPage(target) {
  if (target < 1 || target > pages.value) return
  page.value = target
  load()
}

async function rerun(doc) {
  try {
    await api.runDocument(doc.id)
    toast('已重新提交流水线')
    await load()
  } catch (error) {
    toast(error.message, 'error')
  }
}

function askDelete(doc) {
  deleteTarget.value = doc
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await api.deleteDocument(deleteTarget.value.id)
    toast('文档已删除')
    deleteTarget.value = null
    if (items.value.length === 1 && page.value > 1) page.value -= 1
    await load()
  } catch (error) {
    toast(error.message, 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  load()
  pollTimer = window.setInterval(() => {
    if (processingDoc.value) load()
  }, 2000)
})

onUnmounted(() => {
  if (pollTimer) window.clearInterval(pollTimer)
})
</script>

<style scoped>
.upload-card {
  border: 1.5px dashed #d8cba9;
  border-radius: var(--radius);
  background: #fbf8f1;
  padding: 20px 24px;
  margin-bottom: 18px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.upload-card:hover,
.upload-card.dragging {
  border-color: var(--gold);
  background: #faf4e6;
}

.upload-card.dragging {
  box-shadow: 0 0 0 4px rgba(199, 164, 92, 0.12);
}

.upload-card.busy {
  cursor: wait;
}

.upload-inner {
  display: flex;
  align-items: center;
  gap: 18px;
}

.upload-icon {
  width: 52px;
  height: 52px;
  flex: none;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #fff;
  border: 1px solid #e9ddc0;
  color: var(--gold-deep);
}

.upload-copy {
  flex: 1;
  min-width: 0;
}

.upload-title {
  font-family: var(--serif);
  font-size: 15px;
  color: var(--ink);
  margin-bottom: 3px;
}

.upload-sub {
  font-size: 11.5px;
  color: var(--muted);
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 9px;
}

.upload-file {
  font-size: 11px;
  color: var(--ink-3);
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-progress .progress {
  flex: 1;
  max-width: 320px;
}

.upload-percent {
  font-size: 11px;
  color: var(--gold-deep);
  font-variant-numeric: tabular-nums;
}

.upload-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex: none;
}

.filter-card {
  padding: 18px 22px 14px;
  margin-bottom: 18px;
}

.filter-grid {
  display: grid;
  grid-template-columns: 150px 150px minmax(240px, 1fr) auto;
  gap: 16px;
  align-items: end;
}

.search-box {
  position: relative;
}

.search-box svg {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--faint);
}

.search-box .input {
  padding-left: 33px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.filter-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border-top: 1px solid var(--line-soft);
  padding-top: 12px;
  margin-top: 14px;
  font-size: 11.5px;
  color: var(--muted);
}

.filter-summary strong {
  color: var(--ink);
  font-family: var(--serif);
  font-size: 14px;
}

.running {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--gold-deep);
}

.spin {
  width: 10px;
  height: 10px;
  border: 1.5px solid #d9c79c;
  border-top-color: var(--gold-deep);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.table-card {
  overflow: hidden;
}

.doc-cell {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 240px;
}

.file-mark {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  flex: none;
  display: grid;
  place-items: center;
  background: #f4f2ec;
  color: var(--ink-3);
  border: 1px solid var(--line);
}

.file-mark[data-region='HK'] {
  color: #7b5d20;
  background: #faf3e2;
  border-color: #eadcbb;
}

.file-mark[data-region='MO'] {
  color: var(--success);
  background: var(--success-soft);
  border-color: #d6e8df;
}

.file-mark[data-region='OVERSEAS'] {
  color: var(--info);
  background: var(--info-soft);
  border-color: #dbe6f0;
}

.doc-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.doc-name {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink);
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-name:hover {
  color: var(--gold-deep);
}

.doc-file {
  font-size: 10px;
  color: var(--faint);
  max-width: 320px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tiny {
  font-size: 10.5px;
  color: var(--faint);
  white-space: nowrap;
}

.progress-cell {
  min-width: 130px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.progress-text {
  font-size: 10px;
  color: var(--muted);
  white-space: nowrap;
}

.score-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-cell strong {
  font-family: var(--serif);
  font-size: 15px;
  color: var(--ink);
  min-width: 24px;
}

.score-bar {
  display: block;
  width: 46px;
  height: 3px;
  border-radius: 3px;
  background: #f0ece3;
  overflow: hidden;
}

.score-bar span {
  display: block;
  height: 100%;
  background: var(--success);
}

.score-bar span.low {
  background: var(--danger);
}

.review-pill {
  display: inline-grid;
  place-items: center;
  min-width: 21px;
  height: 19px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 10.5px;
  font-weight: 600;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  white-space: nowrap;
}

.link-btn.danger {
  color: var(--danger);
}

.link-btn.danger:hover {
  color: #9f3f28;
}

.link-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.right {
  text-align: right;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 18px;
  border-top: 1px solid var(--line-soft);
}

.pager-info {
  font-size: 11.5px;
  color: var(--muted);
}

.pager-actions {
  display: flex;
  gap: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1000px) {
  .filter-grid {
    grid-template-columns: 1fr 1fr;
  }
  .filter-search {
    grid-column: span 2;
  }
  .filter-actions {
    grid-column: span 2;
    justify-content: flex-end;
  }
}

@media (max-width: 720px) {
  .upload-inner {
    flex-wrap: wrap;
  }
  .upload-side {
    display: none;
  }
  .filter-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .filter-search,
  .filter-actions {
    grid-column: auto;
  }
  .filter-actions {
    justify-content: flex-start;
  }
  .filter-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>
