import { useEffect, useState } from 'react'
import { BarChart3, TrendingUp } from 'lucide-react'
import ConsumptionChart from '../charts/ConsumptionChart'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { formatTimestamp } from '../utils/dates'
import { getPeaks, getTrends } from '../services/api'
import { useLanguage } from '../utils/i18n'

export default function Analytics() {
  const { t } = useLanguage()
  const [data, setData] = useState(null)
  const [peaks, setPeaks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [period, setPeriod] = useState('day')
  const [selectedDay, setSelectedDay] = useState('')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [selectedYear, setSelectedYear] = useState('')

  useEffect(() => {
    Promise.all([getTrends(), getPeaks(10)])
      .then(([trends, peakData]) => {
        setData(trends)
        setPeaks(peakData.items || [])
        const latest = trends.daily?.at(-1)?.timestamp?.slice(0, 10) || new Date().toISOString().slice(0, 10)
        setSelectedDay(latest)
        setSelectedMonth(latest.slice(0, 7))
        setSelectedYear(latest.slice(0, 4))
      })
      .catch(() => setError('Unable to load energy analytics. Check FastAPI and MongoDB.'))
      .finally(() => setLoading(false))
  }, [])

  const chartData = period === 'day'
    ? (data?.hourly || []).filter(item => item.timestamp?.slice(0, 10) === selectedDay)
    : period === 'month'
      ? (data?.daily || []).filter(item => item.timestamp?.slice(0, 7) === selectedMonth)
      : (data?.monthly || []).filter(item => item.timestamp?.slice(0, 4) === selectedYear)

  const empty = (
    <div className="empty-chart">
      <BarChart3 size={24} />
      <span>No observations are available for this chart.</span>
    </div>
  )

  return (
    <>
      <header className="page-header">
        <div>
          <div className="eyebrow">{t('analyticsEyebrow', 'WORKSPACE · ANALYTICS')}</div>
          <h1>{t('analyticsHeading', 'Energy Analytics')}</h1>
          <p>{t('analyticsSub', 'Explore historical consumption patterns and peak demand.')}</p>
        </div>
        <div className="analytics-period-controls">
          <div className="segmented">
          {['day', 'month', 'year'].map(tab => (
            <button
              key={tab}
              className={period === tab ? 'selected' : ''}
              onClick={() => setPeriod(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
          </div>
          {period === 'day' && <input aria-label="Select day" type="date" value={selectedDay} onChange={event => setSelectedDay(event.target.value)} />}
          {period === 'month' && <input aria-label="Select month" type="month" value={selectedMonth} onChange={event => setSelectedMonth(event.target.value)} />}
          {period === 'year' && <input aria-label="Select year" type="number" min="2000" max="2100" value={selectedYear} onChange={event => setSelectedYear(event.target.value)} />}
        </div>
      </header>

      {loading && <LoadingState label="Loading energy analytics…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <div className="analytics-grid">
          {/* Primary chart — switches based on tab */}
          <section className="panel wide" style={{ gridColumn: 'span 2' }}>
            <div className="panel-heading">
              <div>
                <h2>
                  {period === 'day' ? 'Hourly consumption' : period === 'month' ? 'Daily consumption' : 'Monthly consumption'}
                </h2>
                <p>
                  {period === 'day' ? `Selected day: ${selectedDay} · kW` : period === 'month' ? `Selected month: ${selectedMonth} · kW` : `Selected year: ${selectedYear} · kW`}
                </p>
              </div>
              <span className="mini-label">
                {period === 'day' ? '24 HOURS' : period === 'month' ? 'DAYS IN MONTH' : '12 MONTHS'}
              </span>
            </div>
            <div className="chart-area large">
              {chartData.length ? <ConsumptionChart data={chartData} /> : empty}
            </div>
          </section>

          {/* Weekday vs Weekend */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>{t('weekdayVsWeekend', 'Weekday vs weekend')}</h2>
                <p>Mean active power · kW</p>
              </div>
            </div>
            <div className="compare-list">
              {(data?.patterns?.weekday_weekend || []).map(x => (
                <div className="compare-row" key={x.period}>
                  <span>{x.period}</span>
                  <b>{x.average} kW</b>
                </div>
              ))}
              {!data?.patterns?.weekday_weekend?.length && <p className="muted">No historical data available.</p>}
            </div>
          </section>

          {/* Peak table */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>{t('topPeaks', 'Top peak periods')}</h2>
                <p>{t('topPeaksSub', 'Highest raw active power measurements · kW')}</p>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>RANK</th>
                    <th>TIMESTAMP</th>
                    <th>DEMAND</th>
                  </tr>
                </thead>
                <tbody>
                  {peaks.map((x, i) => (
                    <tr key={x.timestamp}>
                      <td><span className="rank">0{i + 1}</span></td>
                      <td>{formatTimestamp(x.timestamp)}</td>
                      <td className="demand-cell">{x.demand} kW</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!peaks.length && <div className="table-empty">No peak observations available.</div>}
            </div>
          </section>
        </div>
      )}
    </>
  )
}
