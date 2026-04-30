import React from 'react'

export default function SelectorDiff({ before, after }) {
  if (!before && !after) return null
  return (
    <div style={{
      background: 'var(--bg)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
      fontFamily: 'var(--font-mono)',
      fontSize: 12,
    }}>
      {before && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '7px 12px',
          background: 'rgba(255,77,77,0.05)',
          borderBottom: after ? '1px solid var(--border)' : 'none',
        }}>
          <span style={{ color: 'var(--bug)', fontWeight: 700, fontSize: 13, width: 14 }}>−</span>
          <code style={{ color: '#ff8080', wordBreak: 'break-all' }}>{before}</code>
        </div>
      )}
      {after && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          padding: '7px 12px',
          background: 'rgba(0,229,160,0.05)',
        }}>
          <span style={{ color: 'var(--healed)', fontWeight: 700, fontSize: 13, width: 14 }}>+</span>
          <code style={{ color: 'var(--healed)', wordBreak: 'break-all' }}>{after}</code>
        </div>
      )}
    </div>
  )
}
