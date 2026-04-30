import { useState, useEffect, useCallback } from 'react'
import { fetchHeals } from '../lib/api'

export function useHeals(pollInterval = 10000) {
  const [heals, setHeals] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const load = useCallback(async () => {
    const data = await fetchHeals(100)
    setHeals(data.heals || [])
    setTotal(data.total || 0)
    setLastUpdated(new Date())
    setLoading(false)
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, pollInterval)
    return () => clearInterval(id)
  }, [load, pollInterval])

  const stats = {
    healed:      heals.filter(h => h.status === 'healed').length,
    failed:      heals.filter(h => h.status === 'failed').length,
    quarantined: heals.filter(h => h.status === 'quarantined').length,
    needs_review:heals.filter(h => h.status === 'needs_review').length,
    timeSaved:   Math.round(heals.reduce((s, h) => s + (h.time_saved_minutes || 0), 0)),
    avgConfidence: (() => {
      const withConf = heals.filter(h => h.confidence != null)
      if (!withConf.length) return 0
      return Math.round(withConf.reduce((s, h) => s + h.confidence, 0) / withConf.length * 100)
    })(),
  }

  return { heals, total, loading, lastUpdated, stats, refresh: load }
}
