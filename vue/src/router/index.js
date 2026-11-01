import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '运营总览', crumb: '概览' }
  },
  {
    path: '/documents',
    name: 'documents',
    component: () => import('../views/Documents.vue'),
    meta: { title: '文档中心', crumb: '文档中心' }
  },
  {
    path: '/documents/:id',
    name: 'document-detail',
    component: () => import('../views/DocumentDetail.vue'),
    meta: { title: '文档详情', crumb: '文档详情' }
  },
  {
    path: '/review',
    name: 'review',
    component: () => import('../views/Review.vue'),
    meta: { title: '复核工作台', crumb: '复核工作台' }
  },
  {
    path: '/qa',
    name: 'qa',
    component: () => import('../views/Qa.vue'),
    meta: { title: '知识问答', crumb: '知识问答' }
  },
  {
    path: '/risk',
    name: 'risk',
    component: () => import('../views/Risk.vue'),
    meta: { title: '风控中心', crumb: '风控中心' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.afterEach((to) => {
  document.title = `${to.meta.title || '智识中枢'} · 人寿海外`
})

export default router
