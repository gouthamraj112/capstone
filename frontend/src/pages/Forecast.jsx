import { useEffect, useState } from 'react'
import { Activity, TrendingUp } from 'lucide-react'
import { Area, AreaChart, CartesianGrid, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { getEvaluation, getForecast } from '../services/api'
import { formatClock } from '../utils/dates'
import { useLanguage } from '../utils/i18n'
import AnimatedCounter from '../components/AnimatedCounter'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'rgba(15,21,37,0.95)',
      border: '1px solid rgba(45,212,191,0.2)',
      borderRadius: 10,
      padding: '12px 16px',
      backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    }}>
      <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 6 }}>{label}</div>
      {payload.map((entry, i) => (
        <div key={i} style={{ color: entry.color, fontSize: 12, fontWeight: 600, marginBottom: 2 }}>
          {entry.name}: {Number(entry.value).toFixed(2)} kW
        </div>
      ))}
    </div>
  )
}

export default function Forecast() {
  const { t } = useLanguage()
  const [hours, setHours] = useState(6)
  const [data, setData] = useState([])
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError('')
    getForecast(hours)
      .then(result => {
        setData(result.items || [])
        setNote(result.error || result.model || '')
      })
      .catch(() => setError('Forecast request failed. Check FastAPI and MongoDB.'))
      .finally(() => setLoading(false))

    getEvaluation().then(setMetrics).catch(() => {})
  }, [hours])

  const avgForecast = data.length
    ? (data.reduce((s, d) => s + (d.predicted_demand || 0), 0) / data.length)
    : null

  return (
    <>
      <header className="page-header">
        <div>
          <div className="eyebrow">{t('forecastEyebrow', 'WORKSPACE · PREDICTIVE')}</div>
          <h1>{t('forecastHeading', 'Demand Forecast')}</h1>
          <p>{t('forecastSub', 'Explainable seasonal-naive forecast based on the previous day\'s hourly profile.')}</p>
        </div>
        <div className="segmented">
          {[1, 6, 12, 24].map(value => (
            <button
              className={hours === value ? 'selected' : ''}
              key={value}
              onClick={() => setHours(value)}
            >
              {value}h
            </button>
          ))}
        </div>
      </header>

      {error && <ErrorState message={error} />}

      <div className="metric-grid forecast-metrics">
        <div className="small-kpi metric-card">
          <span>{t('forecastHorizon', 'Forecast horizon')}</span>
          <b>{hours} hours</b>
        </div>
        <div className="small-kpi metric-card">
          <span>Model</span>
          <b className="method-text">Seasonal naive</b>
        </div>
        <div className="small-kpi metric-card">
          <span>MAE</span>
          <b>{metrics?.forecast?.mae != null ? <><AnimatedCounter value={Number(metrics.forecast.mae)} /> kW</> : '—'}</b>
        </div>
        <div className="small-kpi metric-card">
          <span>MAPE</span>
          <b>{metrics?.forecast?.mape == null ? '—' : <><AnimatedCounter value={Number(metrics.forecast.mape)} />%</>}</b>
        </div>
        {avgForecast != null && (
          <div className="small-kpi metric-card">
            <span>Avg. predicted</span>
            <b style={{ color: 'var(--accent-cyan)' }}><AnimatedCounter value={avgForecast} /> kW</b>
          </div>
        )}
        <div className="small-kpi metric-card">
          <span>Periods</span>
          <b><AnimatedCounter value={data.length} decimals={0} /></b>
        </div>
      </div>

      <section className="panel" style={{ padding: '18px 20px' }}>
        <div className="panel-heading">
          <div>
            <h2>{t('predictedDemand', 'Predicted demand')}</h2>
            <p>{t('pointEstimate', 'Point estimate and recent variability interval · kW')}</p>
          </div>
          <span className="mini-label">
            {loading ? 'LOADING' : data.length ? `${data.length} PERIODS` : 'NO FORECAST'}
          </span>
        </div>
        <div className="chart-area forecast-chart">
          {loading ? (
            <LoadingState label="Calculating forecast…" />
          ) : data.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data.map(item => ({ ...item, time: formatClock(item.timestamp) }))}
                margin={{ top: 20, right: 12, left: -12, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="forecastBand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="time" tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area dataKey="upper_bound" name="Upper bound" stroke="rgba(45,212,191,0.3)" fill="url(#forecastBand)" />
                <Area dataKey="lower_bound" name="Lower bound" stroke="rgba(45,212,191,0.3)" fill="rgba(5,8,16,0.5)" />
                <Line
                  dataKey="predicted_demand" name="Forecast (kW)"
                  stroke="#22d3ee" strokeWidth={2.5}
                  dot={{ r: 4, fill: '#22d3ee', stroke: '#050810', strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: '#22d3ee', stroke: '#050810', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <Activity size={26} />
              <b>Forecast not available</b>
              <span>{note || 'Ingest at least 24 hourly readings to forecast demand.'}</span>
            </div>
          )}
        </div>
      </section>

      <p className="method-note">
        The interval uses recent observed variability; it is a demonstration interval, not a calibrated probability interval.
      </p>
    </>
  )
}
