import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 25000
})

api.interceptors.response.use(
  response => {
    const res = response.data
    if (res && typeof res === 'object' && 'data' in res && res.data && typeof res.data === 'object' && !Array.isArray(res.data)) {
      return { ...res.data, ...res }
    }
    return res
  },
  error => Promise.reject(error)
)

export const getDashboard = () => api.get('/dashboard')
export const getTrends = () => api.get('/energy/trends')
export const getPeaks = (limit = 10) => api.get('/energy/peaks', { params: { limit } })
export const getAnomalies = (limit = 100) => api.get('/anomalies', { params: { limit } })
export const getAnomalyDetail = id => api.get(`/anomalies/${id}`)
export const getForecast = hours => api.get('/forecast', { params: { hours } })
export const ask = (question, language = 'en') => api.post('/query', { question, language })
export const runAgents = (task = 'insights', hours = 6, language = 'en') => api.post('/agents/run', { task, hours, language })
export const getEvaluation = () => api.get('/evaluation')
export const getTrace = id => api.get(`/agents/trace/${id}`)
export const health = () => api.get('/health')

export default api
