import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatDate } from '../utils/dates'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'rgba(15,21,37,0.95)',
      border: '1px solid rgba(34,211,238,0.2)',
      borderRadius: 10,
      padding: '10px 14px',
      backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    }}>
      <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 4 }}>{label}</div>
      <div style={{ color: '#22d3ee', fontSize: 15, fontWeight: 700 }}>
        {Number(payload[0].value).toLocaleString(undefined, { maximumFractionDigits: 2 })} kW
      </div>
    </div>
  )
}

export default function ConsumptionChart({ data = [] }) {
  const rows = data.map(x => ({ ...x, time: formatDate(x.timestamp) }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={rows} margin={{ top: 10, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="powerFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.25} />
            <stop offset="50%" stopColor="#2dd4bf" stopOpacity={0.08} />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="time" tickLine={false} axisLine={false}
          tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
        />
        <YAxis
          tickLine={false} axisLine={false}
          tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone" dataKey="demand"
          stroke="#22d3ee" strokeWidth={2.5}
          fill="url(#powerFill)" connectNulls
          activeDot={{ r: 5, fill: '#22d3ee', stroke: '#050810', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
