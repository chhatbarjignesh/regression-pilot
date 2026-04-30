import React from 'react'

export default function ConfidenceBar({ value }) {
  if (value == null) return <span style={{ color: 'var(--muted)' }}>—</span>
  const pct = Math.round(value * 100)
  const color = pct >= 75 ? 'var(--healed)' : pct >= 50 ? 'var(--flaky)' : 'var(--bug)'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        width: 60, height: 3,
        background: 'var(--border)',
        borderRadius: 2,
        overflow: 'hidden',
        flexShrink: 0,
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: color,
          borderRadius: 2,
          transition: 'width 0.4s ease',
        }} />
      </div>
      <span style={{ color, fontSize: 11, fontWeight: 600 }}>{pct}%</span>
    </div>
  )
}
