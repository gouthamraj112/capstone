import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import AnimatedCounter from './AnimatedCounter'

export default function MetricCard({ label, value, unit, meta, change, tone = 'teal', icon: Icon }) {
  const up = Number(change) >= 0
  const numericValue = value != null ? Number(String(value).replace(/,/g, '')) : null
  const isNumeric = numericValue != null && !isNaN(numericValue)

  return (
    <article className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <span className={`metric-icon ${tone}`}>
          <Icon size={18} />
        </span>
      </div>
      <div className="metric-number">
        {value == null ? '—' : (
          isNumeric
            ? <AnimatedCounter value={numericValue} />
            : value
        )}
        <small>{value == null ? '' : unit}</small>
      </div>
      <div className="metric-foot">
        {change != null && (
          <span className={up ? 'change-up' : 'change-down'}>
            {up ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(change)}%
          </span>
        )}
        <span>{meta || 'No readings available'}</span>
      </div>
    </article>
  )
}
