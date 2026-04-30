import React, { useState, useMemo } from 'react'
import { useHeals } from './hooks/useHeals'
import MetricCard from './components/MetricCard'
import StatusBadge from './components/StatusBadge'
import ConfidenceBar from './components/ConfidenceBar'
import SelectorDiff from './components/SelectorDiff'
import HealDrawer from './components/HealDrawer'
import { ActivityChart, FrameworkChart } from './components/Charts'

const FILTERS = ['all', 'healed', 'failed', 'needs_review', 'quarantined']

export default function App() {
  const { heals, loading, lastUpdated, stats, refresh } = useHeals(15000)
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    return heals.filter(h => {
      if (filter !== 'all' && h.status !== filter) return false
      if (search && !h.test_name.toLowerCase().includes(search.toLowerCase()) &&
          !h.test_file.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
  }, [heals, filter, search])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* ── Top bar ── */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 28px', height: 52,
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg)',
        position: 'sticky', top: 0, zIndex: 30,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Logo mark */}
          <div style={{
            width: 22, height: 22, position: 'relative',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{
              width: 22, height: 22, borderRadius: '50%',
              border: '1.5px solid var(--healed)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--healed)' }} />
            </div>
          </div>
          <span style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 800, fontSize: 15,
            letterSpacing: '-0.02em',
            color: 'var(--text)',
          }}>
            RegressionPilot
          </span>
          <span style={{
            fontSize: 9, color: 'var(--muted)', letterSpacing: '0.1em',
            border: '1px solid var(--border)', padding: '1px 6px', borderRadius: 2,
          }}>v0.1</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {lastUpdated && (
            <span style={{ fontSize: 10, color: 'var(--muted)' }}>
              updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={refresh}
            style={{
              background: 'none', border: '1px solid var(--border)',
              color: 'var(--muted)', padding: '4px 12px',
              borderRadius: 'var(--radius)', fontSize: 10,
              letterSpacing: '0.06em', textTransform: 'uppercase',
            }}
          >
            Refresh
          </button>
        </div>
      </header>

      <main style={{ flex: 1, padding: '24px 28px', maxWidth: 1280, width: '100%', margin: '0 auto' }}>

        {/* ── Metric cards ── */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 10, marginBottom: 20,
        }}>
          <MetricCard label="Auto-healed" value={stats.healed} accent="var(--healed)" />
          <MetricCard label="Bugs filed" value={stats.failed} accent="var(--bug)" />
          <MetricCard label="Quarantined" value={stats.quarantined} accent="var(--flaky)" />
          <MetricCard label="Needs review" value={stats.needs_review} accent="var(--review)" />
          <MetricCard label="Time saved" value={stats.timeSaved} unit="min" accent="var(--healed)" />
          <MetricCard label="Avg confidence" value={`${stats.avgConfidence}%`} />
        </div>

        {/* ── Charts row ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 10, marginBottom: 20 }}>
          <ActivityChart heals={heals} />
          <FrameworkChart heals={heals} />
        </div>

        {/* ── Heal log ── */}
        <div style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius2)',
          overflow: 'hidden',
        }}>

          {/* Table toolbar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '12px 16px',
            borderBottom: '1px solid var(--border)',
            flexWrap: 'wrap',
          }}>
            <span style={{ fontSize: 10, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, marginRight: 4 }}>
              Heal log
            </span>

            {/* Filter pills */}
            <div style={{ display: 'flex', gap: 4 }}>
              {FILTERS.map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  style={{
                    background: filter === f ? 'var(--bg3)' : 'none',
                    border: `1px solid ${filter === f ? 'var(--border2)' : 'transparent'}`,
                    color: filter === f ? 'var(--text)' : 'var(--muted)',
                    padding: '3px 10px', borderRadius: 2,
                    fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.06em',
                  }}
                >
                  {f.replace('_', ' ')}
                </button>
              ))}
            </div>

            {/* Search */}
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="search tests…"
              style={{
                marginLeft: 'auto',
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                color: 'var(--text)',
                padding: '4px 10px',
                borderRadius: 'var(--radius)',
                fontSize: 11,
                width: 180,
                fontFamily: 'var(--font-mono)',
              }}
            />
          </div>

          {/* Table */}
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)', fontSize: 12 }}>
              Loading…
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)', fontSize: 12 }}>
              No results
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Status', 'Test', 'Selector diff', 'Confidence', 'Saved', 'Jira', 'PR'].map(h => (
                    <th key={h} style={{
                      padding: '8px 14px', textAlign: 'left',
                      fontSize: 9, color: 'var(--muted)',
                      fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((heal, i) => (
                  <tr
                    key={heal.run_id}
                    onClick={() => setSelected(heal)}
                    style={{
                      borderBottom: '1px solid var(--border)',
                      cursor: 'pointer',
                      background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                      transition: 'background 0.12s',
                      animation: 'slide-in 0.2s ease',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg3)'}
                    onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)'}
                  >
                    <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                      <StatusBadge status={heal.status} />
                    </td>
                    <td style={{ padding: '10px 14px', maxWidth: 220 }}>
                      <div style={{ fontWeight: 600, fontSize: 12, marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {heal.test_name}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {heal.test_file}
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px', maxWidth: 240 }}>
                      <SelectorDiff before={heal.selector_before} after={heal.selector_after} />
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <ConfidenceBar value={heal.confidence} />
                    </td>
                    <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                      {heal.time_saved_minutes > 0
                        ? <span style={{ color: 'var(--healed)', fontSize: 12, fontWeight: 600 }}>{heal.time_saved_minutes}m</span>
                        : <span style={{ color: 'var(--muted)' }}>—</span>
                      }
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {heal.jira_ticket
                        ? <span style={{ color: 'var(--review)', fontSize: 11 }}>{heal.jira_ticket}</span>
                        : <span style={{ color: 'var(--muted)' }}>—</span>
                      }
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {heal.pr_url
                        ? (
                          <a
                            href={heal.pr_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={e => e.stopPropagation()}
                            style={{ color: 'var(--healed)', fontSize: 10, textDecoration: 'underline' }}
                          >
                            ↗ PR
                          </a>
                        )
                        : <span style={{ color: 'var(--muted)' }}>—</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div style={{ padding: '8px 16px', borderTop: '1px solid var(--border)', fontSize: 10, color: 'var(--muted)' }}>
            {filtered.length} of {heals.length} events
          </div>
        </div>
      </main>

      {/* ── Detail drawer ── */}
      {selected && <HealDrawer heal={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
