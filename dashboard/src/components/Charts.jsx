import React, { useMemo } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts'

function buildDailyData(heals) {
  const map = {}
  heals.forEach(h => {
    const day = h.timestamp
      ? new Date(h.timestamp).toLocaleDateString('en', { month: 'short', day: 'numeric' })
      : 'Unknown'
    if (!map[day]) map[day] = { day, healed: 0, bugs: 0, flaky: 0 }
    if (h.status === 'healed') map[day].healed++
    else if (h.status === 'failed') map[day].bugs++
    else if (h.status === 'quarantined') map[day].flaky++
  })
  return Object.values(map).slice(-7)
}

const TIP_STYLE = {
  background: '#1a1a1a',
  border: '1px solid #2a2a2a',
  borderRadius: 4,
  fontSize: 11,
  fontFamily: 'JetBrains Mono, monospace',
  color: '#e8e8e8',
}

export function ActivityChart({ heals }) {
  const data = useMemo(() => buildDailyData(heals), [heals])
  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius2)', padding: '16px 20px' }}>
      <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, marginBottom: 14 }}>
        Heal activity — last 7 days
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={data} margin={{ top: 4, right: 0, left: -28, bottom: 0 }}>
          <defs>
            <linearGradient id="gHealed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00e5a0" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00e5a0" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="day" tick={{ fill: '#555', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#555', fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip contentStyle={TIP_STYLE} cursor={{ stroke: '#2a2a2a' }} />
          <Area type="monotone" dataKey="healed" stroke="#00e5a0" strokeWidth={1.5} fill="url(#gHealed)" dot={false} name="Healed" />
          <Area type="monotone" dataKey="bugs" stroke="#ff4d4d" strokeWidth={1} fill="none" dot={false} name="Bugs" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function FrameworkChart({ heals }) {
  const data = useMemo(() => {
    const pw = heals.filter(h => h.framework === 'playwright').length
    const se = heals.filter(h => h.framework === 'selenium').length
    return [
      { name: 'Playwright', value: pw, color: '#7b8cff' },
      { name: 'Selenium',   value: se, color: '#f5a623' },
    ]
  }, [heals])

  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 'var(--radius2)', padding: '16px 20px' }}>
      <div style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, marginBottom: 14 }}>
        By framework
      </div>
      <ResponsiveContainer width="100%" height={80}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="name" tick={{ fill: '#888', fontSize: 11 }} axisLine={false} tickLine={false} width={72} />
          <Tooltip contentStyle={TIP_STYLE} cursor={{ fill: '#1a1a1a' }} />
          <Bar dataKey="value" radius={2} name="Tests">
            {data.map((d, i) => <Cell key={i} fill={d.color} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
