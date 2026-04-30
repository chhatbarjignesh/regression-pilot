import React from 'react'

export default function MetricCard({ label, value, unit = '', accent }) {
  return (
    <div style={{
      background: 'var(--bg2)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius2)',
      padding: '16px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
    }}>
      <span style={{ fontSize: 10, color: 'var(--muted)', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 600 }}>
        {label}
      </span>
      <span style={{ fontSize: 28, fontWeight: 700, fontFamily: 'var(--font-display)', color: accent || 'var(--text)', lineHeight: 1.1 }}>
        {value}
        {unit && <span style={{ fontSize: 13, color: 'var(--muted)', marginLeft: 4, fontFamily: 'var(--font-mono)' }}>{unit}</span>}
      </span>
    </div>
  )
}
