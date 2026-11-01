import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000
})

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && body.code === 0) return body.data
    return Promise.reject(new Error((body && body.msg) || '请求失败'))
  },
  (error) => {
    const body = error.response && error.response.data
    const message = (body && body.msg) || (error.code === 'ECONNABORTED' ? '请求超时，请稍后重试' : '网络异常，请确认后端服务已启动')
    return Promise.reject(new Error(message))
  }
)

export const api = {
  getStatus: () => http.get('/system/status'),
  getDashboard: () => http.get('/dashboard/overview'),
  getDocuments: (params) => http.get('/documents', { params }),
  getDocument: (id) => http.get(`/documents/${id}`),
  uploadDocument: (formData, onUploadProgress) =>
    http.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
      onUploadProgress
    }),
  runDocument: (id) => http.post(`/documents/${id}/run`),
  deleteDocument: (id) => http.delete(`/documents/${id}`),
  getReviewTasks: (params) => http.get('/review/tasks', { params }),
  getReviewStats: () => http.get('/review/stats'),
  resolveTask: (id, payload) => http.post(`/review/tasks/${id}/resolve`, payload),
  ask: (question, top_k = 5) => http.post('/qa/ask', { question, top_k }),
  getSuggestions: () => http.get('/qa/suggestions'),
  riskCheck: (text) => http.post('/risk/check', { text }),
  getRiskOverview: () => http.get('/risk/overview'),
  getAuditLogs: (params) => http.get('/audit/logs', { params })
}

export default api
