<template>
  <div class="page">
    <div class="page-head">
      <div>
        <div class="eyebrow">Retrieval-Augmented QA</div>
        <h1 class="page-title">知识问答</h1>
        <div class="page-sub">双轨混合检索 · 条款引用可溯源 · 多 Agent 合规护栏全程在线</div>
      </div>
      <div class="page-actions">
        <span class="engine-pill">
          <span class="engine-dot"></span>
          {{ engineLabel }}
        </span>
      </div>
    </div>

    <section class="qa-shell">
      <div class="card chat-card">
        <div class="chat-head">
          <div>
            <div class="card-title"><span class="rule"></span>条款问答会话</div>
            <div class="card-sub" style="margin-top: 5px">回答仅基于已收录条款，引用 Top {{ topK }} 切片</div>
          </div>
          <span class="chip outline">演示环境 · 非真实投保建议</span>
        </div>

        <div ref="scrollRef" class="chat-scroll">
          <div class="msg assistant">
            <div class="avatar">智</div>
            <div class="bubble">
              <div class="bubble-head">
                <span class="bubble-name">智识中枢</span>
                <span class="bubble-time">在线</span>
              </div>
              <div class="answer-text">
                您好，我是人寿海外条款知识助手。可以询问等待期、犹豫期、责任免除、理赔材料与时效、健康告知、核保、退保及港澳地区规则等问题。
              </div>
              <div class="answer-text muted" style="margin-top: 8px">
                每个回答都会附上条款出处、检索得分与置信度；涉及收益承诺或敏感话题时将触发合规拦截。
              </div>
            </div>
          </div>

          <div v-for="message in messages" :key="message.id" class="msg" :class="message.role">
            <div v-if="message.role === 'assistant'" class="avatar">智</div>
            <div class="bubble" :class="{ blocked: message.blocked, failed: message.failed }">
              <div class="bubble-head">
                <span class="bubble-name">{{ message.role === 'user' ? '我' : '智识中枢' }}</span>
                <StatusBadge v-if="message.role === 'assistant' && message.mode" type="mode" :value="message.mode" size="sm" />
              </div>

              <div class="answer-text" :class="{ 'user-text': message.role === 'user' }">{{ message.text }}</div>

              <template v-if="message.role === 'assistant' && message.blocked">
                <div class="blocked-banner">
                  <span class="blocked-tag">风控拦截</span>
                  该问题命中敏感话题，已停止生成并写入审计日志。
                </div>
                <div v-if="message.risk_hits && message.risk_hits.length" class="risk-hits">
                  <span v-for="hit in message.risk_hits" :key="hit.term" class="chip outline">{{ hit.category }} · {{ hit.term }}</span>
                </div>
              </template>

              <template v-else-if="message.role === 'assistant' && !message.failed">
                <div v-if="message.confidence != null" class="confidence-row">
                  <span class="confidence-label">回答置信度</span>
                  <div class="progress conf-bar" :class="confidenceTone(message.confidence)">
                    <span :style="{ width: message.confidence * 100 + '%' }"></span>
                  </div>
                  <strong class="confidence-value">{{ Math.round(message.confidence * 100) }}%</strong>
                  <span v-if="message.mode_label" class="mode-text">{{ message.mode_label }}</span>
                </div>

                <div v-if="message.citations && message.citations.length" class="citations">
                  <div class="citations-head">
                    条款引用
                    <span>{{ message.citations.length }} 条 · {{ message.rerank_mode || '加权分数' }}</span>
                  </div>
                  <router-link
                    v-for="(cite, idx) in message.citations"
                    :key="idx"
                    :to="`/documents/${cite.doc_id}`"
                    class="cite"
                  >
                    <span class="cite-index">{{ idx + 1 }}</span>
                    <div class="cite-main">
                      <div class="cite-title">{{ cite.doc_title }}</div>
                      <div class="cite-heading">{{ cite.heading }}</div>
                      <div class="cite-snippet">{{ cite.snippet }}</div>
                    </div>
                    <div class="cite-score">
                      <span>{{ Math.round(cite.score * 100) }}</span>
                      <small>匹配分</small>
                    </div>
                  </router-link>
                </div>

                <div v-if="message.compliance_note" class="compliance-note">
                  <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M8 2l5.5 2.6v3.7c0 3.2-2.2 5.5-5.5 6.7-3.3-1.2-5.5-3.5-5.5-6.7V4.6z" />
                    <path d="M8 6v2.6M8 10.8v.2" stroke-linecap="round" />
                  </svg>
                  {{ message.compliance_note }}
                </div>
              </template>
            </div>
            <div v-if="message.role === 'user'" class="avatar user-avatar">我</div>
          </div>

          <div v-if="loading" class="msg assistant">
            <div class="avatar">智</div>
            <div class="bubble typing">
              <span></span><span></span><span></span>
              <em>正在检索双轨知识底座并生成合规回答…</em>
            </div>
          </div>
        </div>

        <div class="chat-input">
          <textarea
            v-model="question"
            class="textarea ask-area"
            rows="2"
            maxlength="800"
            placeholder="例如：寰宇人生终身寿险的等待期是多久？（Enter 发送，Shift + Enter 换行）"
            @keydown.enter.exact.prevent="send()"
          ></textarea>
          <div class="input-foot">
            <span class="input-hint">{{ question.length }} / 800 · 回答不构成投保建议</span>
            <button class="btn btn-primary" :disabled="!question.trim() || loading" @click="send()">
              <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M2.5 8h10M8.5 3.5L13 8l-4.5 4.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              {{ loading ? '检索中…' : '发送提问' }}
            </button>
          </div>
        </div>
      </div>

      <aside class="qa-side">
        <div class="card side-card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>推荐问题</div>
            <span class="side-tag">8 条</span>
          </div>
          <div class="suggest-list">
            <button
              v-for="(item, idx) in suggestions"
              :key="item.id"
              class="suggest"
              :disabled="loading"
              @click="askSuggestion(item.question)"
            >
              <span class="suggest-no">{{ String(idx + 1).padStart(2, '0') }}</span>
              <span class="suggest-main">
                <span class="suggest-text">{{ item.question }}</span>
                <span class="suggest-tag">{{ item.tag }}</span>
              </span>
            </button>
            <div v-if="!suggestions.length" class="side-empty">推荐问题加载中…</div>
          </div>
        </div>

        <div class="card side-card">
          <div class="card-head">
            <div class="card-title"><span class="rule"></span>检索机制</div>
          </div>
          <div class="mech-body">
            <div class="mech-item">
              <span class="mech-dot gold"></span>
              <div><strong>向量轨</strong><span>字符 n-gram 哈希 512 维 · L2 归一化 · 余弦相似</span></div>
            </div>
            <div class="mech-item">
              <span class="mech-dot blue"></span>
              <div><strong>关键词轨</strong><span>关键词覆盖 + 章节标题命中 + 文档标题加权</span></div>
            </div>
            <div class="mech-item">
              <span class="mech-dot green"></span>
              <div><strong>合规轨</strong><span>敏感话题识别 → 拦截 / 免责声明 → 审计留痕</span></div>
            </div>
            <div class="mech-foot">未命中足够上下文时，系统会如实提示补充条款，而非臆测作答。</div>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'

import api from '../api'
import StatusBadge from '../components/StatusBadge.vue'
import { toast } from '../composables/useToast'

const topK = 5
const messages = ref([])
const suggestions = ref([])
const question = ref('')
const loading = ref(false)
const scrollRef = ref(null)
const actualMode = ref('')
let seq = 0

const engineLabel = computed(() => {
  if (!actualMode.value) return '引擎检测中'
  return actualMode.value === 'llm' ? 'DeepSeek 模型在线' : '本地规则引擎 · 降级运行'
})

function confidenceTone(value) {
  if (value < 0.55) return 'danger'
  if (value < 0.75) return 'gold'
  return 'success'
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  })
}

watch(() => [messages.value.length, loading.value], scrollToBottom)

async function send(text) {
  const content = (text || question.value).trim()
  if (!content || loading.value) return
  messages.value.push({ id: ++seq, role: 'user', text: content })
  question.value = ''
  loading.value = true
  scrollToBottom()
  try {
    const result = await api.ask(content, topK)
    actualMode.value = result.mode
    messages.value.push({
      id: ++seq,
      role: 'assistant',
      text: result.answer,
      citations: result.citations || [],
      confidence: result.confidence,
      mode: result.mode,
      mode_label: result.mode_label,
      compliance_note: result.compliance_note,
      blocked: result.blocked,
      risk_hits: result.risk_hits || [],
      rerank_mode: result.rerank_mode
    })
  } catch (error) {
    messages.value.push({
      id: ++seq,
      role: 'assistant',
      text: `本次检索未能完成：${error.message}`,
      failed: true
    })
    toast(error.message, 'error')
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function askSuggestion(text) {
  if (loading.value) return
  send(text)
}

async function loadSuggestions() {
  try {
    const data = await api.getSuggestions()
    suggestions.value = data.items || []
  } catch (error) {
    toast(error.message, 'error')
  }
}

onMounted(async () => {
  await loadSuggestions()
  try {
    const status = await api.getStatus()
    actualMode.value = status.actual_mode
  } catch (error) {
    // 状态栏失败不阻断问答
  }
})
</script>

<style scoped>
.engine-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--muted);
  font-size: 11.5px;
}

.engine-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  box-shadow: 0 0 0 3px rgba(199, 164, 92, 0.16);
}

.qa-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 322px;
  gap: 18px;
  align-items: start;
}

.chat-card {
  display: flex;
  flex-direction: column;
  min-height: 620px;
  height: calc(100vh - 190px);
  max-height: 900px;
  overflow: hidden;
}

.chat-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 18px 22px 14px;
  border-bottom: 1px solid var(--line-soft);
}

.chat-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: linear-gradient(180deg, #fdfcf9 0%, #ffffff 100%);
}

.msg {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.msg.user {
  justify-content: flex-end;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  flex: none;
  display: grid;
  place-items: center;
  font-family: var(--serif);
  font-size: 13px;
  color: var(--gold-soft);
  background: var(--ink);
  border: 1px solid rgba(199, 164, 92, 0.35);
}

.user-avatar {
  color: var(--ink);
  background: #f4eedf;
  border-color: #e3d4b3;
}

.bubble {
  max-width: min(88%, 720px);
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 12px 12px 12px 4px;
  padding: 13px 16px;
  box-shadow: 0 2px 10px rgba(15, 39, 66, 0.03);
}

.msg.user .bubble {
  background: var(--ink);
  color: #f3efe5;
  border-color: var(--ink);
  border-radius: 12px 12px 4px 12px;
  max-width: min(76%, 620px);
}

.bubble.blocked {
  border-color: #e8c3b8;
  background: #fffbf9;
}

.bubble.failed {
  border-color: #e8c3b8;
  background: var(--danger-soft);
}

.bubble-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 7px;
}

.bubble-name {
  font-family: var(--serif);
  font-size: 12.5px;
  color: var(--ink);
}

.msg.user .bubble-name {
  color: var(--gold-soft);
}

.bubble-time {
  font-size: 10px;
  color: var(--faint);
}

.answer-text {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.9;
  color: #27374a;
}

.msg.user .answer-text {
  color: #f2eee4;
}

.user-text {
  white-space: pre-wrap;
}

.msg.user .bubble-head {
  justify-content: flex-end;
}

.blocked-banner {
  margin-top: 11px;
  background: var(--danger-soft);
  border: 1px solid #efd0c7;
  color: #8c3a28;
  border-radius: 8px;
  padding: 9px 12px;
  font-size: 12px;
  line-height: 1.7;
}

.blocked-tag {
  display: inline-block;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  margin-right: 6px;
}

.risk-hits {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 9px;
}

.confidence-row {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: 13px;
  padding-top: 11px;
  border-top: 1px dashed var(--line-soft);
}

.confidence-label {
  font-size: 10.5px;
  color: var(--muted);
  flex: none;
}

.conf-bar {
  flex: 1;
  max-width: 180px;
}

.confidence-value {
  font-family: var(--serif);
  font-size: 13px;
  color: var(--ink);
  flex: none;
}

.mode-text {
  font-size: 10px;
  color: var(--faint);
  margin-left: auto;
}

.citations {
  margin-top: 13px;
  border-top: 1px dashed var(--line-soft);
  padding-top: 11px;
}

.citations-head {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-3);
  margin-bottom: 9px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.citations-head span {
  font-weight: 400;
  font-size: 10px;
  color: var(--faint);
}

.cite {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 11px;
  border: 1px solid var(--line-soft);
  border-radius: 8px;
  background: #fcfaf5;
  margin-bottom: 7px;
  transition: border-color 0.15s, background 0.15s;
}

.cite:hover {
  border-color: #dfd2b5;
  background: #fbf6ea;
}

.cite-index {
  width: 19px;
  height: 19px;
  flex: none;
  border-radius: 4px;
  background: var(--ink);
  color: var(--gold-soft);
  font-size: 10px;
  display: grid;
  place-items: center;
}

.cite-main {
  min-width: 0;
  flex: 1;
}

.cite-title {
  font-family: var(--serif);
  font-size: 12px;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cite-heading {
  font-size: 10.5px;
  color: var(--gold-deep);
  margin-top: 2px;
}

.cite-snippet {
  font-size: 11px;
  color: var(--muted);
  line-height: 1.65;
  margin-top: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cite-score {
  flex: none;
  text-align: right;
  display: flex;
  flex-direction: column;
}

.cite-score span {
  font-family: var(--serif);
  font-size: 15px;
  color: var(--ink);
}

.cite-score small {
  font-size: 9px;
  color: var(--faint);
}

.compliance-note {
  display: flex;
  gap: 7px;
  align-items: flex-start;
  margin-top: 11px;
  padding: 9px 11px;
  border-radius: 7px;
  background: var(--warn-soft);
  border: 1px solid #efdfba;
  color: #7d5c20;
  font-size: 11.5px;
  line-height: 1.7;
}

.compliance-note svg {
  flex: none;
  margin-top: 3px;
}

.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  min-height: 48px;
}

.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--gold);
  animation: blink 1.2s infinite;
}

.typing span:nth-child(2) {
  animation-delay: 0.18s;
}

.typing span:nth-child(3) {
  animation-delay: 0.36s;
}

.typing em {
  font-style: normal;
  font-size: 11.5px;
  color: var(--muted);
  margin-left: 6px;
}

@keyframes blink {
  0%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-2px);
  }
}

.chat-input {
  border-top: 1px solid var(--line-soft);
  padding: 13px 18px 15px;
  background: #fff;
}

.ask-area {
  min-height: 62px;
  resize: none;
  background: #fcfbf8;
}

.input-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 9px;
}

.input-hint {
  font-size: 10.5px;
  color: var(--faint);
}

.qa-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.side-card {
  overflow: hidden;
}

.side-tag {
  font-size: 10px;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2px 6px;
}

.suggest-list {
  padding: 10px 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.suggest {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 8px;
  padding: 9px 9px;
  transition: background 0.15s, border-color 0.15s;
}

.suggest:hover:not(:disabled) {
  background: #fbf7ec;
  border-color: #eee2c8;
}

.suggest:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.suggest-no {
  font-family: var(--serif);
  font-size: 11px;
  color: var(--gold-deep);
  padding-top: 1px;
  flex: none;
}

.suggest-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.suggest-text {
  font-size: 12px;
  color: var(--ink-2);
  line-height: 1.55;
}

.suggest-tag {
  align-self: flex-start;
  font-size: 9.5px;
  color: #7a6230;
  background: #f5efe0;
  border: 1px solid #e9ddc2;
  border-radius: 3px;
  padding: 0 5px;
}

.side-empty {
  font-size: 11px;
  color: var(--faint);
  padding: 12px;
  text-align: center;
}

.mech-body {
  padding: 13px 18px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mech-item {
  display: flex;
  gap: 9px;
  align-items: flex-start;
}

.mech-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-top: 6px;
  flex: none;
}

.mech-dot.gold {
  background: var(--gold);
}

.mech-dot.blue {
  background: var(--info);
}

.mech-dot.green {
  background: var(--success);
}

.mech-item div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mech-item strong {
  font-size: 12px;
  color: var(--ink-2);
  font-weight: 600;
}

.mech-item span {
  font-size: 10.5px;
  color: var(--muted);
  line-height: 1.6;
}

.mech-foot {
  margin-top: 3px;
  padding-top: 11px;
  border-top: 1px solid var(--line-soft);
  font-size: 10.5px;
  color: var(--faint);
  line-height: 1.7;
}

@media (max-width: 1100px) {
  .qa-shell {
    grid-template-columns: minmax(0, 1fr);
  }
  .chat-card {
    height: auto;
    max-height: none;
    min-height: 640px;
  }
  .chat-scroll {
    max-height: 560px;
  }
  .qa-side {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 820px) {
  .qa-side {
    grid-template-columns: minmax(0, 1fr);
  }
  .bubble {
    max-width: 92%;
  }
  .cite-score {
    display: none;
  }
}
</style>
