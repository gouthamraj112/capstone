import { useState, useMemo } from 'react'
import {
  AreaChart, Area, BarChart, Bar, ResponsiveContainer,
  XAxis, YAxis, Tooltip, CartesianGrid, Cell, Legend
} from 'recharts'
import {
  Activity, ArrowDownRight, ArrowUpRight, BarChart3,
  Calendar, CheckCircle2, ChevronRight, Clock,
  Eye, Layers, Sparkles, Table as TableIcon, TrendingUp, Zap
} from 'lucide-react'

// Custom Dark Glass Tooltip
const PictorialTooltip = ({ active, payload, label, chartType }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload || {}

  return (
    <div className="pictorial-tooltip">
      <div className="tooltip-label">{label || d.label}</div>
      {chartType === 'anomaly' ? (
        <div className="tooltip-metrics">
          <div className="metric-row actual">
            <span>Actual:</span>
            <b>{d.actual?.toFixed(2)} kW</b>
          </div>
          <div className="metric-row expected">
            <span>Expected:</span>
            <b>{d.expected?.toFixed(2)} kW</b>
          </div>
          {d.deviation != null && (
            <div className="metric-row deviation">
              <span>Deviation:</span>
              <b style={{ color: d.deviation > 0 ? '#f43f5e' : '#38bdf8' }}>
                {d.deviation > 0 ? `+${d.deviation.toFixed(2)}` : d.deviation.toFixed(2)} kW
              </b>
            </div>
          )}
          {d.severity && (
            <div className={`severity-tag ${d.severity}`}>
              {d.severity.toUpperCase()} SEVERITY
            </div>
          )}
        </div>
      ) : chartType === 'forecast' ? (
        <div className="tooltip-metrics">
          <div className="metric-row primary">
            <span>Predicted:</span>
            <b>{Number(d.demand || d.predicted_demand || payload[0]?.value).toFixed(2)} kW</b>
          </div>
          {d.lower_bound != null && d.upper_bound != null && (
            <div className="metric-row range">
              <span>95% Range:</span>
              <span>{d.lower_bound.toFixed(2)} – {d.upper_bound.toFixed(2)} kW</span>
            </div>
          )}
        </div>
      ) : (
        <div className="tooltip-metrics">
          <div className="metric-row primary">
            <span>{d.category || 'Demand'}:</span>
            <b>{Number(payload[0]?.value || d.demand || d.value).toFixed(2)} {d.unit || 'kW'}</b>
          </div>
        </div>
      )}
    </div>
  )
}

// Fallback extractor when raw evidence is passed without pre-computed chart_data
function extractFromEvidence(evidence = [], intent = '') {
  if (!Array.isArray(evidence) || !evidence.length) return null

  if (intent === 'forecast') {
    const forecastItems = evidence.filter(e => e.predicted_demand != null || e.timestamp)
    if (forecastItems.length) {
      return {
        type: 'forecast',
        title: `Forecasted Demand (${forecastItems.length}h Horizon)`,
        data: forecastItems.map((f, i) => {
          const ts = String(f.timestamp || '')
          const lbl = ts.length >= 16 ? ts.substring(11, 16) : ts.length >= 5 ? ts.slice(-5) : `t+${i + 1}`
          return {
            label: lbl,
            demand: Number(f.predicted_demand || f.demand || 0),
            lower_bound: Number(f.lower_bound || 0),
            upper_bound: Number(f.upper_bound || 0),
            unit: 'kW'
          }
        })
      }
    }
  }

  if (intent === 'weekday_weekend_comparison') {
    const weekday = evidence.find(e => /weekday/i.test(e.label || ''))?.value
    const weekend = evidence.find(e => /weekend/i.test(e.label || ''))?.value
    if (weekday != null || weekend != null) {
      return {
        type: 'comparison',
        title: 'Weekday vs Weekend Demand',
        data: [
          { label: 'Weekday', demand: Number(weekday || 0), category: 'Weekday', color: '#22d3ee', unit: 'kW' },
          { label: 'Weekend', demand: Number(weekend || 0), category: 'Weekend', color: '#a78bfa', unit: 'kW' }
        ]
      }
    }
  }

  if (intent === 'evening_increase') {
    const evening = evidence.find(e => /evening|18:00/i.test(e.label || ''))?.value
    const baseline = evidence.find(e => /overall|mean/i.test(e.label || ''))?.value
    if (evening != null || baseline != null) {
      return {
        type: 'comparison',
        title: 'Evening Peak vs Baseline Demand',
        data: [
          { label: 'Full-Day Baseline', demand: Number(baseline || 0), category: 'Baseline', color: '#2dd4bf', unit: 'kW' },
          { label: 'Evening Peak (18-21h)', demand: Number(evening || 0), category: 'Evening', color: '#f59e0b', unit: 'kW' }
        ]
      }
    }
  }

  if (intent === 'anomaly_detection') {
    const anomalies = evidence.filter(e => e.actual_value != null || e.anomaly_score != null)
    if (anomalies.length) {
      return {
        type: 'anomaly',
        title: 'Detected Consumption Anomalies',
        data: anomalies.slice(0, 8).map((a, i) => {
          const ts = String(a.timestamp || '')
          const lbl = ts.length >= 16 ? ts.substring(11, 16) : ts.length >= 5 ? ts.slice(-5) : `#${i + 1}`
          return {
            label: lbl,
            actual: Number(a.actual_value || 0),
            expected: Number(a.expected_value || 0),
            deviation: Number(a.deviation || 0),
            severity: a.severity || 'medium',
            unit: 'kW'
          }
        })
      }
    }
  }

  // Peak records
  const peakItems = evidence.filter(e => e.demand != null && !e.label)
  if (peakItems.length) {
    return {
      type: 'bar',
      title: 'Top Peak Demand Records',
      data: peakItems.slice(0, 8).map((p, i) => {
        const ts = String(p.timestamp || '')
        const lbl = ts.length >= 16 ? ts.substring(11, 16) : ts.length >= 5 ? ts.slice(-5) : `Peak ${i + 1}`
        return {
          label: lbl,
          demand: Number(p.demand || 0),
          unit: 'kW'
        }
      })
    }
  }

  // Hourly items
  const hourlyItems = evidence.filter(e => /average demand at/i.test(e.label || ''))
  if (hourlyItems.length) {
    return {
      type: 'hourly',
      title: 'Peak Demand by Hour',
      data: hourlyItems.map(h => ({
        label: (h.label || '').replace(/average demand at\s*/i, ''),
        demand: Number(h.value || 0),
        unit: 'kW'
      }))
    }
  }

  // Generic summary items with numeric values
  const numericItems = evidence.filter(e => typeof e.value === 'number' && e.label)
  if (numericItems.length >= 2) {
    const colors = ['#22d3ee', '#f43f5e', '#f59e0b', '#38bdf8', '#a78bfa', '#10b981']
    return {
      type: 'overview',
      title: 'Smart Grid Demand Profile',
      data: numericItems.slice(0, 6).map((n, i) => ({
        label: n.label,
        demand: Number(n.value),
        color: colors[i % colors.length],
        unit: n.unit || 'kW'
      }))
    }
  }

  return null
}

export default function AssistantPictorial({
  chartData = [],
  chartType = null,
  chartTitle = null,
  intent = '',
  evidence = []
}) {
  const [viewMode, setViewMode] = useState('chart') // 'chart' | 'table'

  // Resolve data and chart configuration
  const resolved = useMemo(() => {
    if (Array.isArray(chartData) && chartData.length > 0) {
      return {
        type: chartType || 'bar',
        title: chartTitle || 'Visual Energy Insight',
        data: chartData
      }
    }
    return extractFromEvidence(evidence, intent)
  }, [chartData, chartType, chartTitle, intent, evidence])

  if (!resolved || !resolved.data || resolved.data.length === 0) {
    return null
  }

  const { type, title, data } = resolved

  // Quick stats calculations
  const stats = useMemo(() => {
    if (type === 'anomaly') {
      const highCount = data.filter(d => d.severity === 'high').length
      const maxDev = Math.max(...data.map(d => Math.abs(d.deviation || 0)))
      return [
        { label: 'Anomalies Plotted', value: data.length },
        { label: 'High Severity', value: highCount, highlight: highCount > 0 ? '#f43f5e' : '#10b981' },
        { label: 'Max Deviation', value: `${maxDev.toFixed(2)} kW` }
      ]
    }
    if (type === 'comparison' && data.length === 2) {
      const d1 = data[0].demand || 0
      const d2 = data[1].demand || 0
      const diffPct = d1 > 0 ? (((d2 - d1) / d1) * 100).toFixed(1) : '0'
      const isPositive = Number(diffPct) > 0
      return [
        { label: data[0].label, value: `${d1.toFixed(2)} kW` },
        { label: data[1].label, value: `${d2.toFixed(2)} kW` },
        {
          label: 'Variance',
          value: `${isPositive ? '+' : ''}${diffPct}%`,
          highlight: isPositive ? '#f59e0b' : '#38bdf8'
        }
      ]
    }
    if (type === 'forecast') {
      const demands = data.map(d => d.demand || 0)
      const max = Math.max(...demands)
      const min = Math.min(...demands)
      const avg = demands.reduce((a, b) => a + b, 0) / (demands.length || 1)
      return [
        { label: 'Forecast Peak', value: `${max.toFixed(2)} kW`, highlight: '#22d3ee' },
        { label: 'Forecast Low', value: `${min.toFixed(2)} kW` },
        { label: 'Mean Projected', value: `${avg.toFixed(2)} kW` }
      ]
    }
    // Bar or Overview
    const values = data.map(d => Number(d.demand || d.value || 0))
    const peak = Math.max(...values)
    const avg = values.reduce((a, b) => a + b, 0) / (values.length || 1)
    return [
      { label: 'Max Recorded', value: `${peak.toFixed(2)} kW`, highlight: '#f43f5e' },
      { label: 'Average', value: `${avg.toFixed(2)} kW` },
      { label: 'Data Points', value: data.length }
    ]
  }, [data, type])

  // Contextual icon
  const IconComponent =
    type === 'forecast' ? TrendingUp :
    type === 'anomaly' ? Activity :
    type === 'comparison' ? Calendar :
    type === 'hourly' ? Clock :
    Zap

  // Determine top value index for bar highlighting
  const peakIndex = useMemo(() => {
    let maxIdx = 0
    let maxVal = -Infinity
    data.forEach((item, i) => {
      const val = Number(item.demand || item.value || 0)
      if (val > maxVal) {
        maxVal = val
        maxIdx = i
      }
    })
    return maxIdx
  }, [data])

  return (
    <div className="assistant-pictorial-card">
      {/* Pictorial Header */}
      <div className="pictorial-header">
        <div className="pictorial-title-group">
          <div className="pictorial-icon-badge">
            <IconComponent size={14} />
          </div>
          <div>
            <h4 className="pictorial-title">{title}</h4>
            <span className="pictorial-subtitle">
              Interactive Smart Grid Visualization · {data.length} observations
            </span>
          </div>
        </div>

        {/* View Toggle */}
        <div className="pictorial-view-toggle">
          <button
            type="button"
            className={`toggle-btn ${viewMode === 'chart' ? 'active' : ''}`}
            onClick={() => setViewMode('chart')}
            title="Visual Chart View"
            aria-label="Visual Chart View"
          >
            <BarChart3 size={12} />
            <span>Chart</span>
          </button>
          <button
            type="button"
            className={`toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
            onClick={() => setViewMode('table')}
            title="Data Table View"
            aria-label="Data Table View"
          >
            <TableIcon size={12} />
            <span>Data</span>
          </button>
        </div>
      </div>

      {/* Pictorial Body */}
      {viewMode === 'chart' ? (
        <div className="pictorial-chart-wrapper">
          {type === 'forecast' ? (
            /* Forecast Area Chart */
            <ResponsiveContainer width="100%" height={210}>
              <AreaChart data={data} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.35} />
                    <stop offset="60%" stopColor="#2dd4bf" stopOpacity={0.10} />
                    <stop offset="100%" stopColor="#22d3ee" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="upperBandFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#a78bfa" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'Inter' }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'Inter' }}
                  tickFormatter={v => `${v} kW`}
                />
                <Tooltip content={<PictorialTooltip chartType="forecast" />} />
                {data[0]?.upper_bound != null && (
                  <Area
                    type="monotone"
                    dataKey="upper_bound"
                    stroke="rgba(167,139,250,0.4)"
                    strokeDasharray="3 3"
                    strokeWidth={1}
                    fill="url(#upperBandFill)"
                    isAnimationActive={true}
                    animationDuration={600}
                  />
                )}
                <Area
                  type="monotone"
                  dataKey="demand"
                  stroke="#22d3ee"
                  strokeWidth={2.5}
                  fill="url(#forecastFill)"
                  activeDot={{ r: 5, fill: '#22d3ee', stroke: '#050810', strokeWidth: 2 }}
                  isAnimationActive={true}
                  animationDuration={800}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : type === 'anomaly' ? (
            /* Anomaly Actual vs Expected Bar/Line Chart */
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={data} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="actualAnomalyGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#f43f5e" stopOpacity={0.3} />
                  </linearGradient>
                  <linearGradient id="expectedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.5} />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.15} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'Inter' }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'Inter' }}
                  tickFormatter={v => `${v} kW`}
                />
                <Tooltip content={<PictorialTooltip chartType="anomaly" />} />
                <Bar
                  dataKey="actual"
                  name="Actual Load"
                  fill="url(#actualAnomalyGrad)"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={22}
                  isAnimationActive={true}
                />
                <Bar
                  dataKey="expected"
                  name="Expected Baseline"
                  fill="url(#expectedGrad)"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={22}
                  isAnimationActive={true}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            /* Standard / Comparison / Overview Bar Chart */
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={data} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="defaultCyanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.95} />
                    <stop offset="100%" stopColor="#0891b2" stopOpacity={0.35} />
                  </linearGradient>
                  <linearGradient id="peakHighlightGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.95} />
                    <stop offset="100%" stopColor="#b45309" stopOpacity={0.35} />
                  </linearGradient>
                  <linearGradient id="purpleGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.95} />
                    <stop offset="100%" stopColor="#6d28d9" stopOpacity={0.35} />
                  </linearGradient>
                  <linearGradient id="roseGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.95} />
                    <stop offset="100%" stopColor="#be123c" stopOpacity={0.35} />
                  </linearGradient>
                  <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.95} />
                    <stop offset="100%" stopColor="#0f766e" stopOpacity={0.35} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="label"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'Inter' }}
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'Inter' }}
                  tickFormatter={v => `${v} kW`}
                />
                <Tooltip content={<PictorialTooltip chartType={type} />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar
                  dataKey="demand"
                  radius={[5, 5, 0, 0]}
                  maxBarSize={type === 'comparison' ? 44 : 26}
                  isAnimationActive={true}
                  animationDuration={700}
                >
                  {data.map((entry, index) => {
                    let fill = 'url(#defaultCyanGrad)'
                    if (entry.color) {
                      fill = entry.color
                    } else if (type === 'comparison') {
                      fill = index === 0 ? 'url(#defaultCyanGrad)' : 'url(#peakHighlightGrad)'
                    } else if (index === peakIndex) {
                      fill = 'url(#peakHighlightGrad)'
                    }
                    return <Cell key={`cell-${index}`} fill={fill} />
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}

          {/* Special Comparison Meter for 2-element comparisons */}
          {type === 'comparison' && data.length === 2 && (
            <div className="pictorial-comparison-meter">
              {data.map((item, idx) => {
                const total = (data[0].demand || 0) + (data[1].demand || 0)
                const pct = total > 0 ? Math.round(((item.demand || 0) / total) * 100) : 50
                const color = idx === 0 ? '#22d3ee' : '#f59e0b'
                return (
                  <div key={idx} className="meter-segment">
                    <div className="meter-info">
                      <span className="meter-label">{item.label}</span>
                      <span className="meter-val">{item.demand?.toFixed(2)} kW ({pct}%)</span>
                    </div>
                    <div className="meter-track">
                      <div className="meter-bar" style={{ width: `${pct}%`, background: color }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      ) : (
        /* Data Breakdown Table View */
        <div className="pictorial-table-wrapper">
          <table className="pictorial-table">
            <thead>
              <tr>
                <th>Item / Time</th>
                {type === 'anomaly' ? (
                  <>
                    <th>Actual</th>
                    <th>Expected</th>
                    <th>Deviation</th>
                    <th>Severity</th>
                  </>
                ) : type === 'forecast' ? (
                  <>
                    <th>Predicted</th>
                    <th>Lower 95%</th>
                    <th>Upper 95%</th>
                  </>
                ) : (
                  <>
                    <th>Demand (kW)</th>
                    <th>Relative Share</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => {
                const totalDemand = data.reduce((s, r) => s + (Number(r.demand || r.actual || 0)), 0)
                const share = totalDemand > 0 ? (((Number(row.demand || row.actual || 0)) / totalDemand) * 100).toFixed(1) : '—'
                return (
                  <tr key={idx}>
                    <td className="row-label">
                      <span className="dot" style={{ background: row.color || (idx === peakIndex ? '#f59e0b' : '#22d3ee') }} />
                      {row.label}
                    </td>
                    {type === 'anomaly' ? (
                      <>
                        <td className="font-mono">{row.actual?.toFixed(2)} kW</td>
                        <td className="font-mono text-muted">{row.expected?.toFixed(2)} kW</td>
                        <td className={`font-mono ${row.deviation > 0 ? 'text-rose' : 'text-cyan'}`}>
                          {row.deviation > 0 ? `+${row.deviation.toFixed(2)}` : row.deviation?.toFixed(2)} kW
                        </td>
                        <td>
                          <span className={`table-severity-pill ${row.severity}`}>
                            {row.severity}
                          </span>
                        </td>
                      </>
                    ) : type === 'forecast' ? (
                      <>
                        <td className="font-mono font-bold text-cyan">{row.demand?.toFixed(2)} kW</td>
                        <td className="font-mono text-muted">{row.lower_bound?.toFixed(2)} kW</td>
                        <td className="font-mono text-muted">{row.upper_bound?.toFixed(2)} kW</td>
                      </>
                    ) : (
                      <>
                        <td className="font-mono font-bold">{Number(row.demand || row.value || 0).toFixed(2)} kW</td>
                        <td className="font-mono text-muted">{share}%</td>
                      </>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pictorial Footer / Stat Summary Chips */}
      <div className="pictorial-footer">
        <div className="pictorial-stat-chips">
          {stats.map((s, idx) => (
            <div key={idx} className="stat-chip">
              <span className="chip-label">{s.label}:</span>
              <b className="chip-val" style={{ color: s.highlight || 'var(--text-primary)' }}>
                {s.value}
              </b>
            </div>
          ))}
        </div>
        <div className="pictorial-badge">
          <Sparkles size={11} />
          <span>Grounded Analytics</span>
        </div>
      </div>
    </div>
  )
}
