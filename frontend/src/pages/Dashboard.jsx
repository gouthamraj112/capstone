import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, AlertTriangle, ArrowUpRight, BarChart3, Clock, Database, Gauge, RefreshCw, TrendingUp, Zap } from 'lucide-react'
import { getDashboard, getTrends, getPeaks, getForecast } from '../services/api'
import MetricCard from '../components/MetricCard'
import ConsumptionChart from '../charts/ConsumptionChart'
import HourlyChart from '../charts/HourlyChart'
import { formatDate, formatTimestamp } from '../utils/dates'
import { useLanguage } from '../utils/i18n'
import { getTimeGreeting } from '../utils/greeting'

const fmt = v => (v == null ? null : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }))

export default function Dashboard() {
  const { lang, t } = useLanguage()
  const [data, setData] = useState(null)
  const [trends, setTrends] = useState(null)
  const [peaks, setPeaks] = useState([])
  const [forecast, setForecast] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [greeting, setGreeting] = useState(() => getTimeGreeting(lang))

  // Live timestamp clock update
  useEffect(() => {
    setGreeting(getTimeGreeting(lang))
    const timer = setInterval(() => {
      setGreeting(getTimeGreeting(lang))
    }, 1000)
    return () => clearInterval(timer)
  }, [lang])

  const load = (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    Promise.all([getDashboard(), getTrends(), getPeaks(5), getForecast(1)])
      .then(([d, t, p, f]) => {
        setData(d)
        setTrends(t)
        setPeaks(p.items || [])
        setForecast(d.forecasted_demand ?? f.items?.[0]?.predicted_demand ?? null)
        setError('')
      })
      .catch(() => setError('Could not reach the API. Check that FastAPI and MongoDB are available.'))
      .finally(() => { setLoading(false); setRefreshing(false) })
  }

  useEffect(() => { load() }, [])

  const noData = !data?.observations

  return (
    <>
      <header className="page-header dashboard-header">
        <div>
          <div className="eyebrow live-eyebrow">
            <span className="live-clock-pill">
              <Clock size={13} className="clock-icon" />
              <span>{greeting.fullStamp}</span>
            </span>
            <span className="eyebrow-divider">·</span>
            <span>{t('overviewEyebrow', 'ENERGY OPERATIONS')}</span>
          </div>
          <h1 className="greeting-title">
            {greeting.text}, Grid Operator <span className="greeting-icon">{greeting.icon}</span>
          </h1>
          <p className="greeting-subtext">
            {greeting.subtext}
          </p>
        </div>
        <div className="header-actions">
          <span className="date-pill">
            <span className="tiny-dot" /> {t('liveData', 'Live data')}
          </span>
          <button
            className="icon-button"
            onClick={() => load(true)}
            title="Refresh data"
            aria-label="Refresh data"
            style={refreshing ? { animation: 'spin 1s linear infinite' } : {}}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </header>

      {loading && (
        <div className="notice">
          <Database size={17} />
          <span>{t('loadingData', 'Loading energy data…')}</span>
        </div>
      )}

      {error && <div className="notice error">{error}</div>}

      {!loading && noData && (
        <div className="notice">
          <Database size={17} />
          <div>
            <b>No energy data yet</b>
            <span>Ingest <code>data/household_power_consumption.txt</code> into local MongoDB to populate dashboard analytics.</span>
          </div>
        </div>
      )}

      <section className="metric-grid dashboard-metrics">
        <MetricCard
          label={t('totalConsumption', 'Total consumption')}
          value={fmt(data?.total_consumption)}
          unit=" kWh"
          meta={t('acrossReadings', 'Across available readings')}
          icon={Zap}
        />
        <MetricCard
          label={t('averageDemand', 'Average demand')}
          value={fmt(data?.average_demand)}
          unit=" kW"
          meta={t('meanActivePower', 'Mean active power')}
          tone="blue"
          icon={Activity}
        />
        <MetricCard
          label={t('peakDemand', 'Peak demand')}
          value={fmt(data?.peak_demand)}
          unit=" kW"
          meta={t('highestObserved', 'Highest observed reading')}
          tone="purple"
          icon={Gauge}
        />
        <MetricCard
          label={t('anomaliesKpi', 'Anomalies')}
          value={data?.anomalies ? Number(data.anomalies).toLocaleString() : null}
          meta={t('detectedPeriods', 'Detected periods')}
          tone="amber"
          icon={AlertTriangle}
        />
        <MetricCard
          label={t('forecastedDemand', 'Forecasted demand')}
          value={fmt(forecast)}
          unit=" kW"
          meta={t('nextHourly', 'Next hourly period')}
          tone="blue"
          icon={TrendingUp}
        />
        <MetricCard
          label={t('dataCoverage', 'Data coverage')}
          value={data?.observations ? t('available', 'Available') : null}
          meta={
            data?.data_coverage?.start
              ? `${formatDate(data.data_coverage.start)} – ${formatDate(data.data_coverage.end)}`
              : t('awaitingReadings', 'Awaiting readings')
          }
          tone="purple"
          icon={Database}
        />
      </section>

      <section className="content-grid main-charts">
        <article className="panel trend-panel">
          <div className="panel-heading">
            <div>
              <h2>{t('consumptionTrend', 'Consumption trend')}</h2>
              <p>{t('averagePowerOverTime', 'Average active power over time')}</p>
            </div>
            <span className="mini-label">FULL HISTORY</span>
          </div>
          <div className="chart-legend">
            <span><i className="legend-line" /> Active power <b>kW</b></span>
          </div>
          <div className="chart-area">
            {trends?.daily?.length ? (
              <ConsumptionChart data={trends.daily} />
            ) : (
              <div className="empty-chart">
                <BarChart3 size={24} />
                <span>Trend appears after dataset ingestion</span>
              </div>
            )}
          </div>
          <div className="chart-bottom">
            <span>{t('historicalDemand', 'Historical energy demand')}</span>
            <Link to="/analytics" className="text-link">
              {t('viewAnalytics', 'View analytics')} <ArrowUpRight size={14} />
            </Link>
          </div>
        </article>

        <article className="panel hourly-panel">
          <div className="panel-heading">
            <div>
              <h2>{t('hourlyProfile', 'Hourly profile')}</h2>
              <p>{t('demandByHour', 'Average demand by hour of day')}</p>
            </div>
            <span className="mini-label">24 HOURS</span>
          </div>
          <div className="chart-area hourly">
            {trends?.patterns?.hourly?.length ? (
              <HourlyChart data={trends.patterns.hourly} />
            ) : (
              <div className="empty-chart">
                <BarChart3 size={22} />
                <span>No readings yet</span>
              </div>
            )}
          </div>
          <div className="hourly-foot">
            <span><i className="legend-line blue-line" />{t('averageDemand', 'Average demand')}</span>
            <span>kW</span>
          </div>
        </article>
      </section>

      <section className="content-grid lower-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{t('peakPeriods', 'Peak demand periods')}</h2>
              <p>{t('highestRecorded', 'Highest recorded readings')}</p>
            </div>
            <Link to="/analytics" className="text-link">
              {t('allPeaks', 'All peaks')} <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>PERIOD</th>
                  <th>DEMAND</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {peaks.slice(0, 5).map((p, i) => (
                  <tr key={p.timestamp}>
                    <td>
                      <span className="rank">0{i + 1}</span>
                      {formatTimestamp(p.timestamp)}
                    </td>
                    <td className="demand-cell">{p.demand} kW</td>
                    <td><span className="status-pill">Peak</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!peaks.length && (
              <div className="table-empty">Peak periods will appear when readings are available.</div>
            )}
          </div>
        </article>

        <article className="insight-card">
          <div className="insight-icon"><Zap size={17} /></div>
          <div className="insight-label">{t('energyInsightTitle', 'ENERGY INSIGHT')}</div>
          <h3>{noData ? 'Insights grounded in your data' : t('startQuestion', 'Start with a question')}</h3>
          <p>
            {noData
              ? 'Once readings are ingested, the assistant can explain peaks, anomalies, and demand patterns with supporting evidence.'
              : t('askExplanation', 'Ask the AI assistant to explain the latest patterns in your readings.')}
          </p>
          <Link to="/assistant">
            {t('openAssistant', 'Open AI assistant')} <ArrowUpRight size={14} />
          </Link>
          <div className="insight-decoration">⚡</div>
        </article>
      </section>

      <div className="footnote">
        <span>
          <i className="status-dot ok" /> {t('dataSourceStatus', 'Data source status')}
        </span>
        <span>
          {data?.observations
            ? `${data.observations.toLocaleString()} ${t('readings', 'readings')}`
            : 'Awaiting dataset ingestion'} <b>·</b> Local MongoDB
        </span>
      </div>
    </>
  )
}
