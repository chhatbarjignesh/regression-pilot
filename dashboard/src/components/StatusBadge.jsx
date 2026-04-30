import React from 'react'

const CONFIG = {
  healed:       { label: 'HEALED',      color: 'var(--healed)', bg: 'var(--healed-bg)' },
  failed:       { label: 'BUG FILED',   color: 'var(--bug)',    bg: 'var(--bug-bg)' },
  quarantined:  { label: 'QUARANTINED', color: 'var(--flaky)',  bg: 'var(--flaky-bg)' },
  needs_review: { label: 'NEEDS REVIEW',color: 'var(--review)', bg: 'var(--review-bg)' },
  pending:      { label: 'PENDING',     color: 'var(--pending)',bg: 'transparent' },
  healing:      { label: 'HEALING…',    color: 'var(--healed)', bg: 'var(--healed-bg)' },
}

export default function StatusBadge({ status }) {
  const cfg = CONFIG[status] || CONFIG.pending
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      padding: '2px 8px',
      borderRadius: 2,
      fontSize: 10,
      fontWeight: 600,
      letterSpacing: '0.08em',
      color: cfg.color,
      background: cfg.bg,
      border: `1px solid ${cfg.color}30`,
      whiteSpace: 'nowrap',
    }}>
      {status === 'healing' && (
        <span style={{
          width: 5, height: 5, borderRadius: '50%',
          background: cfg.color,
          animation: 'pulse-dot 1s infinite',
          flexShrink: 0,
        }} />
      )}
      {cfg.label}
    </span>
  )
}
