import { lazy, Suspense, useEffect, useState } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import Sidebar from './components/Sidebar'
import LanguageSelector from './components/LanguageSelector'
import { health } from './services/api'
import { useLanguage } from './utils/i18n'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Anomalies = lazy(() => import('./pages/Anomalies'))
const Forecast = lazy(() => import('./pages/Forecast'))
const Assistant = lazy(() => import('./pages/Assistant'))
const Trace = lazy(() => import('./pages/Trace'))
const Evaluation = lazy(() => import('./pages/Evaluation'))

export default function App() {
  const [connected, setConnected] = useState(false)
  const [apiOnline, setApiOnline] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { t } = useLanguage()

  const titles = {
    '/': 'Smart Grid Energy Intelligence',
    '/analytics': t('analytics', 'Energy analytics'),
    '/anomalies': t('anomalies', 'Anomaly detection'),
    '/forecast': t('forecast', 'Demand forecast'),
    '/assistant': t('assistant', 'AI assistant'),
    '/trace': t('trace', 'Agent trace'),
    '/evaluation': t('evaluation', 'Evaluation'),
  }

  useEffect(() => {
    health().then(result => {
      setConnected(Boolean(result.mongodb))
      setApiOnline(true)
    }).catch(() => {
      setConnected(false)
      setApiOnline(false)
    })
  }, [])

  return (
    <div className="app-shell">
      {mobileOpen && (
        <button 
          className="mobile-backdrop" 
          aria-label="Close navigation" 
          onClick={() => setMobileOpen(false)} 
        />
      )}
      <Sidebar 
        connected={connected} 
        mobileOpen={mobileOpen} 
        onNavigate={() => setMobileOpen(false)} 
      />
      <main className="main">
        <div className="topbar">
          <div className="mobile-brand"><span>✳</span> gridwise</div>
          <button 
            className="mobile-menu" 
            aria-label="Open navigation" 
            onClick={() => setMobileOpen(true)}
          >
            <Menu />
          </button>
          <div className="crumb">
            {t('workspace', 'Workspace')} <span>/</span> <b>{titles[location.pathname] || titles['/']}</b>
          </div>
          <div className="top-actions">
            <span className={`api-state ${apiOnline ? 'connected' : ''}`}>
              <i />{apiOnline ? t('apiOnline', 'API reachable') : t('apiOffline', 'API offline')}
            </span>
            <LanguageSelector />
            <div className="top-avatar">SG</div>
          </div>
        </div>
        <div className="page-content">
          <Suspense fallback={<div className="loading-state">{t('loadingData', 'Loading page…')}</div>}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/anomalies" element={<Anomalies />} />
              <Route path="/forecast" element={<Forecast />} />
              <Route path="/assistant" element={<Assistant />} />
              <Route path="/trace" element={<Trace />} />
              <Route path="/evaluation" element={<Evaluation />} />
            </Routes>
          </Suspense>
        </div>
      </main>
    </div>
  )
}
