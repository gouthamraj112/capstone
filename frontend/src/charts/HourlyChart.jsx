import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'rgba(15,21,37,0.95)',
      border: '1px solid rgba(56,189,248,0.2)',
      borderRadius: 10,
      padding: '10px 14px',
      backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    }}>
      <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 4 }}>{label}:00</div>
      <div style={{ color: '#38bdf8', fontSize: 15, fontWeight: 700 }}>
        {Number(payload[0].value).toLocaleString(undefined, { maximumFractionDigits: 2 })} kW
      </div>
    </div>
  )
}

export default function HourlyChart({ data = [], xKey = 'hour' }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 12, right: 6, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.9} />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.3} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey={xKey}
          tickFormatter={v => xKey === 'hour' ? `${v}:00` : v}
          tickLine={false} axisLine={false}
          tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
        />
        <YAxis
          tickLine={false} axisLine={false}
          tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
        <Bar dataKey="average" fill="url(#barGrad)" radius={[6, 6, 0, 0]} maxBarSize={28} />
      </BarChart>
    </ResponsiveContainer>
  )
}
