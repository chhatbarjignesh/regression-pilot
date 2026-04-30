import React from 'react'
import StatusBadge from './StatusBadge'
import ConfidenceBar from './ConfidenceBar'
import SelectorDiff from './SelectorDiff'

function Row({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>{label}</span>
      <div style={{ color: 'var(--text)', fontSize: 12 }}>{children}</div>
    </div>
  )
}

export default function HealDrawer({ heal, onClose }) {
  if (!heal) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.6)',
          zIndex: 40,
          animation: 'slide-in 0.15s ease',
        }}
      />
      {/* Panel */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0,
        width: 480,
        background: 'var(--bg2)',
        borderLeft: '1px solid var(--border)',
        zIndex: 50,
        overflowY: 'auto',
        animation: 'slide-in 0.2s ease',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky', top: 0,
          background: 'var(--bg2)',
          zIndex: 1,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <StatusBadge status={heal.status} />
            <span style={{ fontSize: 10, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>
              {heal.run_id}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: '1px solid var(--border)',
              color: 'var(--muted)', padding: '4px 10px',
              borderRadius: 'var(--radius)', fontSize: 11,
            }}
          >
            ESC
          </button>
        </div>

        <div style={{ padding: '0 20px 40px' }}>
          <Row label="Test name">
            <span style={{ fontWeight: 600 }}>{heal.test_name}</span>
          </Row>
          <Row label="File">
            <code style={{ color: 'var(--review)', fontSize: 11 }}>{heal.test_file}</code>
          </Row>
          <Row label="Framework">
            <span style={{
              display: 'inline-block',
              padding: '2px 8px',
              background: 'var(--bg3)',
              border: '1px solid var(--border)',
              borderRadius: 2,
              fontSize: 11,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}>{heal.framework}</span>
          </Row>

          {heal.confidence != null && (
            <Row label="AI confidence">
              <ConfidenceBar value={heal.confidence} />
            </Row>
          )}

          {(heal.selector_before || heal.selector_after) && (
            <Row label="Selector diff">
              <SelectorDiff before={heal.selector_before} after={heal.selector_after} />
            </Row>
          )}

          {heal.time_saved_minutes > 0 && (
            <Row label="Estimated time saved">
              <span style={{ color: 'var(--healed)', fontWeight: 600 }}>
                {heal.time_saved_minutes} min
              </span>
            </Row>
          )}

          {heal.retries > 0 && (
            <Row label="Retries">{heal.retries}</Row>
          )}

          {heal.jira_ticket && (
            <Row label="Jira ticket">
              <span style={{ color: 'var(--review)' }}>{heal.jira_ticket}</span>
            </Row>
          )}

          {heal.pr_url && (
            <Row label="Pull request">
              <a
                href={heal.pr_url}
                target="_blank"
                rel="noreferrer"
                style={{ color: 'var(--healed)', textDecoration: 'underline', fontSize: 11 }}
              >
                {heal.pr_url.replace('https://github.com/', '')}
              </a>
            </Row>
          )}

          {heal.commit_sha && (
            <Row label="Commit">
              <code style={{ color: 'var(--muted)' }}>{heal.commit_sha}</code>
            </Row>
          )}

          {heal.error && (
            <Row label="Note">
              <span style={{ color: 'var(--muted)', fontSize: 11 }}>{heal.error}</span>
            </Row>
          )}

          {heal.timestamp && (
            <Row label="Time">
              <span style={{ color: 'var(--muted)' }}>
                {new Date(heal.timestamp).toLocaleString()}
              </span>
            </Row>
          )}
        </div>
      </div>
    </>
  )
}
