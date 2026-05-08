import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const uploadFile = (type: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/uploads/${type}`, form)
}

export const getUploadStatus = () => api.get('/uploads/status').then(r => r.data)
export const getMonths = () => api.get('/dashboard/months').then(r => r.data)
export const getTeams = () => api.get('/dashboard/teams').then(r => r.data)

export const getKPIs = (team: string, months?: string) =>
  api.get('/dashboard/kpis', { params: { team, months } }).then(r => r.data)

export const getYTDKPIs = (team: string) =>
  api.get('/dashboard/kpis/ytd', { params: { team } }).then(r => r.data)

export const getMonthlyTrend = (team: string) =>
  api.get('/dashboard/charts/monthly-trend', { params: { team } }).then(r => r.data)

export const getDeptComparison = (months?: string) =>
  api.get('/dashboard/charts/department-comparison', { params: { months } }).then(r => r.data)

export const getDownloadsVsReuse = (team: string) =>
  api.get('/dashboard/charts/downloads-vs-reuse', { params: { team } }).then(r => r.data)

export const getPendingTrend = (team: string) =>
  api.get('/dashboard/charts/pending-feedback-trend', { params: { team } }).then(r => r.data)

export const getLeaderboard = (team: string, months?: string, topN = 5) =>
  api.get('/dashboard/leaderboard', { params: { team, months, top_n: topN } }).then(r => r.data)

export const getMissingSavings = (team: string, patMonths?: string, savingsMonths?: string) =>
  api.get('/governance/missing-savings', { params: { team, pat_months: patMonths, savings_months: savingsMonths } }).then(r => r.data)

export const getPendingFeedback = (team: string) =>
  api.get('/governance/pending-feedback', { params: { team } }).then(r => r.data)

export const exportExcel = (team: string, months?: string) =>
  api.get('/exports/excel', { params: { team, months }, responseType: 'blob' })

export const exportPDF = (team: string, months?: string) =>
  api.get('/exports/pdf', { params: { team, months }, responseType: 'blob' })

export const exportPNG = (team: string, chartType: string, months?: string) =>
  api.get('/exports/png', { params: { team, chart_type: chartType, months }, responseType: 'blob' })

export const sendMail = (data: { recipients: string[]; subject: string; body: string }) =>
  api.post('/mail/send', data).then(r => r.data)

export const previewPendingFeedbackMail = (signums: string[], team: string) =>
  api.post('/mail/pending-feedback/preview', { signums, team }).then(r => r.data)

export const sendPendingFeedbackMail = (signums: string[], team: string) =>
  api.post('/mail/pending-feedback/send', { signums, team }).then(r => r.data)

export const getAuthStatus = () => api.get('/auth/status').then(r => r.data)
export const startDeviceFlow = () => api.post('/auth/device-flow').then(r => r.data)
export const setGraphToken = (token: string) => api.post('/auth/token', { token }).then(r => r.data)

export default api
