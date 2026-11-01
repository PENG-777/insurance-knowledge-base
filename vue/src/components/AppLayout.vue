<template>
  <div class="shell">
    <aside class="sidebar" :class="{ open: drawerOpen }">
      <div class="brand">
        <div class="brand-mark">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.3">
            <path d="M12 2.8l7.4 3.1v5.2c0 4.4-3.1 7.6-7.4 9.1-4.3-1.5-7.4-4.7-7.4-9.1V5.9z" />
            <path d="M8.5 12l2.3 2.3 4.7-5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <div class="brand-text">
          <div class="brand-name">人寿海外 · 智识中枢</div>
          <div class="brand-en">Insurance Knowledge Intelligence</div>
        </div>
      </div>

      <div class="nav-label">工作空间</div>
      <nav class="nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item) }"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.55" v-html="item.icon"></svg>
          <span>{{ item.label }}</span>
          <span v-if="item.badge && status" class="nav-badge">{{ status.pending_reviews }}</span>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <div class="mini-card">
          <div class="mini-head">
            <span class="pulse"></span>
            <span>知识底座运行中</span>
          </div>
          <div class="mini-row"><span>文档资产</span><strong>{{ status ? status.documents : '—' }}</strong></div>
          <div class="mini-row"><span>知识对象</span><strong>{{ status ? status.entities : '—' }}</strong></div>
          <div class="mini-row"><span>待复核</span><strong class="gold">{{ status ? status.pending_reviews : '—' }}</strong></div>
        </div>
        <div class="sidebar-foot">
          <span>v1.0</span>
          <span>演示环境 · 数据为演示</span>
        </div>
      </div>
    </aside>

    <div v-if="drawerOpen" class="scrim" @click="drawerOpen = false"></div>

    <div class="main">
      <header class="topbar">
        <div class="topbar-left">
          <button class="menu-btn" aria-label="打开导航" @click="drawerOpen = !drawerOpen">
            <svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.7">
              <path d="M4 7h16M4 12h16M4 17h16" stroke-linecap="round" />
            </svg>
          </button>
          <div class="crumb">
            <span class="crumb-root">人寿海外 · 智识中枢</span>
            <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" stroke-width="1.4">
              <path d="M4.5 2.5L8 6l-3.5 3.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <strong>{{ route.meta.crumb || route.meta.title }}</strong>
          </div>
        </div>

        <div class="topbar-right">
          <span class="status-chip" :class="{ error: statusError }" :title="statusHint">
            <span class="status-dot"></span>
            {{ statusLabel }}
          </span>
          <span class="mode-chip" :data-mode="mode">
            <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.4">
              <path d="M8 1.8l1.5 3.6 3.6 1.5-3.6 1.5L8 12l-1.5-3.6L2.9 6.9l3.6-1.5z" stroke-linejoin="round" />
            </svg>
            {{ modeLabel }}
          </span>
          <span class="demo-chip">DEMO</span>
          <div class="avatar" title="复核员 陈保怡">陈</div>
        </div>
      </header>

      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import api from '../api'

const route = useRoute()
const drawerOpen = ref(false)
const status = ref(null)
const statusError = ref('')
let timer = null

const navItems = [
  {
    to: '/',
    label: '运营总览',
    icon:
      '<rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/>'
  },
  {
    to: '/documents',
    label: '文档中心',
    icon:
      '<path d="M6 2.8h7.2L18 7.6v13.6H6z"/><path d="M13 3v5h5"/><path d="M9 12h6M9 15.5h6" stroke-linecap="round"/>'
  },
  {
    to: '/review',
    label: '复核工作台',
    badge: true,
    icon:
      '<path d="M12 3l7 3v6c0 4.2-2.9 7.4-7 9-4.1-1.6-7-4.8-7-9V6z"/><path d="M8.7 12l2.2 2.2 4.3-4.6" stroke-linecap="round" stroke-linejoin="round"/>'
  },
  {
    to: '/qa',
    label: '知识问答',
    icon:
      '<path d="M4 5.5h16v10.5H9l-5 4z" stroke-linejoin="round"/><path d="M8 9.5h8M8 12.5h5" stroke-linecap="round"/>'
  },
  {
    to: '/risk',
    label: '风控中心',
    icon:
      '<path d="M12 3l8 3.5v5.2c0 4.6-3.3 8-8 9.3-4.7-1.3-8-4.7-8-9.3V6.5z"/><path d="M12 8v4.5M12 16v.3" stroke-linecap="round"/>'
  }
]

const isActive = (item) => (item.to === '/' ? route.path === '/' : route.path.startsWith(item.to))

const mode = computed(() => (status.value && status.value.actual_mode) || 'mock')
const modeLabel = computed(() => (mode.value === 'llm' ? 'DeepSeek 在线' : '本地规则引擎'))
const statusLabel = computed(() => {
  if (statusError.value) return '服务异常'
  return status.value ? '服务正常' : '连接中'
})
const statusHint = computed(() => {
  if (statusError.value) return statusError.value
  if (!status.value) return '正在连接后端服务'
  return status.value.last_error || '后端服务运行正常'
})

async function loadStatus() {
  try {
    status.value = await api.getStatus()
    statusError.value = ''
  } catch (error) {
    statusError.value = error.message
  }
}

watch(
  () => route.path,
  () => {
    drawerOpen.value = false
  }
)

onMounted(() => {
  loadStatus()
  timer = window.setInterval(loadStatus, 30000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.shell {
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-w);
  z-index: 40;
  display: flex;
  flex-direction: column;
  background: var(--ink);
  color: #e9edf3;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  padding: 0 14px 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 22px 8px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
  margin-bottom: 18px;
}

.brand-mark {
  width: 39px;
  height: 39px;
  border: 1px solid rgba(199, 164, 92, 0.65);
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: var(--gold);
  flex: none;
  background: rgba(199, 164, 92, 0.08);
}

.brand-text {
  min-width: 0;
}

.brand-name {
  font-family: var(--serif);
  font-size: 14.5px;
  letter-spacing: 0.02em;
  color: #f7f3ea;
  line-height: 1.35;
  white-space: nowrap;
}

.brand-en {
  font-size: 8px;
  color: rgba(255, 255, 255, 0.44);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-top: 3px;
  white-space: nowrap;
}

.nav-label {
  font-size: 10px;
  letter-spacing: 0.18em;
  color: rgba(255, 255, 255, 0.36);
  padding: 0 10px;
  margin-bottom: 8px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px 11px;
  border-radius: 8px;
  font-size: 13px;
  color: rgba(235, 240, 246, 0.7);
  transition: all 0.16s ease;
  border-left: 2px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.055);
  color: #fff;
}

.nav-item.active {
  background: rgba(199, 164, 92, 0.12);
  border-left-color: var(--gold);
  color: #f4e4bf;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex: none;
  opacity: 0.85;
}

.nav-badge {
  margin-left: auto;
  min-width: 20px;
  height: 17px;
  padding: 0 5px;
  border-radius: 9px;
  display: inline-grid;
  place-items: center;
  background: rgba(199, 164, 92, 0.18);
  color: #e5cd94;
  font-size: 10.5px;
  font-weight: 600;
}

.sidebar-bottom {
  margin-top: auto;
  padding-top: 16px;
}

.mini-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.035);
  border-radius: 10px;
  padding: 12px 13px;
}

.mini-head {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.65);
  margin-bottom: 10px;
}

.pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #63b896;
  box-shadow: 0 0 0 3px rgba(99, 184, 150, 0.14);
}

.mini-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.46);
}

.mini-row strong {
  color: #f2f5f9;
  font-family: var(--serif);
  font-size: 14px;
  font-weight: 600;
}

.mini-row strong.gold {
  color: var(--gold);
}

.sidebar-foot {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 4px 0;
  font-size: 9.5px;
  color: rgba(255, 255, 255, 0.28);
  letter-spacing: 0.05em;
}

.main {
  margin-left: var(--sidebar-w);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 30px;
  background: rgba(246, 243, 236, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}

.menu-btn {
  display: none;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  place-items: center;
  padding: 0;
}

.crumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--faint);
  min-width: 0;
}

.crumb-root {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.crumb svg {
  flex: none;
  opacity: 0.55;
}

.crumb strong {
  color: var(--ink);
  font-weight: 600;
  white-space: nowrap;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: none;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  color: var(--success);
  border: 1px solid #d7e7df;
  background: #f2f8f5;
  padding: 4px 9px;
  border-radius: 6px;
  white-space: nowrap;
}

.status-chip.error {
  color: var(--danger);
  border-color: #efd0c7;
  background: var(--danger-soft);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-dot 2s ease infinite;
}

.mode-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  border: 1px solid #e6d8b7;
  background: #f9f2e2;
  color: #7b5d20;
  padding: 4px 9px;
  border-radius: 6px;
  white-space: nowrap;
}

.mode-chip[data-mode='mock'] {
  border-color: var(--line);
  background: #faf8f3;
  color: var(--muted);
}

.demo-chip {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--gold-deep);
  border: 1px dashed #d9c79c;
  padding: 3px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--ink);
  color: #f3e7c9;
  display: grid;
  place-items: center;
  font-family: var(--serif);
  font-size: 12px;
  border: 1px solid rgba(199, 164, 92, 0.5);
}

.content {
  flex: 1;
}

.scrim {
  position: fixed;
  inset: 0;
  z-index: 35;
  background: rgba(15, 39, 66, 0.35);
  backdrop-filter: blur(1px);
}

@keyframes pulse-dot {
  0%,
  100% {
    box-shadow: 0 0 0 0 currentColor;
    opacity: 1;
  }
  50% {
    box-shadow: 0 0 0 3px transparent;
    opacity: 0.75;
  }
}

@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-102%);
    transition: transform 0.24s ease;
    box-shadow: 20px 0 50px rgba(15, 39, 66, 0.18);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .main {
    margin-left: 0;
  }

  .topbar {
    padding: 0 16px;
    height: 60px;
  }

  .menu-btn {
    display: grid;
  }

  .crumb-root {
    display: none;
  }

  .status-chip {
    display: none;
  }

  .demo-chip {
    display: none;
  }
}

@media (max-width: 560px) {
  .mode-chip {
    display: none;
  }

  .topbar-right {
    gap: 8px;
  }
}
</style>
