import { NavLink } from 'react-router-dom'
import { Activity, AlertTriangle, Bot, ChartNoAxesCombined, ChevronDown, CircleHelp, ClipboardList, Gauge, LayoutDashboard, Radio, Zap } from 'lucide-react'
import { useLanguage } from '../utils/i18n'

export default function Sidebar({ connected, mobileOpen = false, onNavigate = () => {} }) {
  const { t } = useLanguage()

  const items = [
    { to: '/', key: 'dashboard', label: t('dashboard', 'Dashboard'), icon: LayoutDashboard, desc: 'Overview & KPIs' },
    { to: '/analytics', key: 'analytics', label: t('analytics', 'Analytics'), icon: ChartNoAxesCombined, desc: 'Energy trends' },
    { to: '/anomalies', key: 'anomalies', label: t('anomalies', 'Anomalies'), icon: AlertTriangle, desc: 'Detection' },
    { to: '/forecast', key: 'forecast', label: t('forecast', 'Forecast'), icon: Activity, desc: 'Predictions' },
    { to: '/assistant', key: 'assistant', label: t('assistant', 'AI Assistant'), icon: Bot, live: true, desc: 'Ask anything' },
    { to: '/trace', key: 'trace', label: t('trace', 'Agent Trace'), icon: Radio, desc: 'Agent flow' },
    { to: '/evaluation', key: 'evaluation', label: t('evaluation', 'Evaluation'), icon: ClipboardList, desc: 'Model metrics' },
  ]

  return (
    <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="brand">
        <div className="brand-mark"><Zap size={20} fill="currentColor" /></div>
        <div><b>gridwise</b><span>ENERGY INTELLIGENCE</span></div>
        <ChevronDown className="brand-chevron" size={15} />
      </div>
      <div className="workspace">
        <span className="workspace-dot" /> {t('workspace', 'Local workspace')} <ChevronDown size={14} />
      </div>
      <div className="nav-caption">{t('workspaceTag', 'WORKSPACE')}</div>
      <nav>
        {items.map(({ to, label, icon: Icon, live }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={onNavigate}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={17} />
            <span>{label}</span>
            {live && <em className="live-tag">LIVE</em>}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="data-status">
          <div className="status-line">
            <span className={`status-dot ${connected ? 'ok' : 'offline'}`} />
            <span>{connected ? t('mongoConnected', 'MongoDB connected') : t('mongoOffline', 'MongoDB offline')}</span>
          </div>
          <small>Local data source</small>
        </div>
        <a className="help-button" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
          <CircleHelp size={16} /> {t('apiDocs', 'API documentation')} <span>↗</span>
        </a>
        <div className="profile">
          <div className="avatar">SG</div>
          <div><b>Smart Grid Lab</b><small>Local demo</small></div>
          <Gauge size={16} />
        </div>
      </div>
    </aside>
  )
}
