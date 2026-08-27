import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Uploads / long-running semantic-index building can take longer -
// scanned PDFs go through OCR + embedding generation, which the app
// itself advertises support for up to 50MB. 120s was cutting off large
// or scanned papers before the backend had a real chance to finish;
// 5 minutes gives that legitimate work room without masking an actually
// broken/hung request forever.
const longClient = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

export function setAuthToken(token) {
  const header = token ? `Bearer ${token}` : null
  for (const c of [client, longClient]) {
    if (header) {
      c.defaults.headers.common.Authorization = header
    } else {
      delete c.defaults.headers.common.Authorization
    }
  }
}

// If a token expires mid-session, force back to login rather than showing
// confusing partial/blank pages.
function handleAuthError(error) {
  if (error?.response?.status === 401) {
    localStorage.removeItem('rexplore-token')
    setAuthToken(null)
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
  }
  return Promise.reject(error)
}

client.interceptors.response.use((r) => r, handleAuthError)
longClient.interceptors.response.use((r) => r, handleAuthError)

export const api = {
  // Auth
  register: (fullName, email, password, confirmPassword) =>
    client.post('/auth/register', {
      full_name: fullName,
      email,
      password,
      confirm_password: confirmPassword,
    }),
  login: (email, password) => client.post('/auth/login', { email, password }),
  logout: () => client.post('/auth/logout'),
  me: () => client.get('/auth/me'),
  updateProfile: (fullName, affiliation) => client.patch('/auth/me', { full_name: fullName, affiliation }),
  updateEmail: (newEmail, currentPassword) => client.patch('/auth/me/email', { new_email: newEmail, current_password: currentPassword }),
  updatePassword: (currentPassword, newPassword, confirmNewPassword) =>
    client.patch('/auth/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_new_password: confirmNewPassword,
    }),
  uploadAvatar: (file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/auth/me/avatar', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  removeAvatar: () => client.delete('/auth/me/avatar'),
  deleteAccount: (currentPassword) => client.delete('/auth/me', { data: { current_password: currentPassword } }),

  // Papers
  uploadPaper: (file, onProgress) => {
    const form = new FormData()
    form.append('file', file)
    return longClient.post('/papers/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded * 100) / evt.total))
      },
    })
  },
  listPapers: () => client.get('/papers'),
  getPaper: (id) => client.get(`/papers/${id}`),
  // File endpoints require the auth header, so plain <a href> links can't
  // hit them directly - fetch as a blob and open/download that instead.
  openPaperFile: async (id) => {
    const res = await longClient.get(`/papers/${id}/file`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(res.data)
    window.open(url, '_blank', 'noopener')
    setTimeout(() => window.URL.revokeObjectURL(url), 60000)
  },
  comparePapers: (paperIds) => client.post('/papers/compare', { paper_ids: paperIds }),

  // Queries
  askQuestion: (paperId, question) => longClient.post('/queries', { paper_id: paperId, question }),
  getQueryHistory: (paperId) => client.get(`/queries/paper/${paperId}`),

  // Datasets
  getDatasetsForPaper: (paperId) => client.get(`/datasets/paper/${paperId}`),
  refreshDatasetSearch: (datasetId) => longClient.get(`/datasets/${datasetId}/search`),
  createSyntheticDataset: (datasetId, payload) => client.post(`/datasets/${datasetId}/synthetic`, payload),
  downloadSyntheticDataset: async (syntheticId) => {
    const res = await client.get(`/datasets/synthetic/${syntheticId}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(res.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `synthetic_dataset_${syntheticId}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    setTimeout(() => window.URL.revokeObjectURL(url), 60000)
  },

  // Analytics
  getAnalyticsOverview: () => client.get('/analytics/overview'),
  getAnalyticsFeatures: () => client.get('/analytics/features'),

  // Health
  health: () => client.get('/health'),
}

export default api
