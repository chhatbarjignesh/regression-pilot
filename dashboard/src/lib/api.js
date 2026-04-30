const BASE = import.meta.env.VITE_API_URL || '/api'

export async function fetchHeals(limit = 50) {
  try {
    const res = await fetch(`${BASE}/heals?limit=${limit}`)
    if (!res.ok) throw new Error('API error')
    return res.json()
  } catch {
    // Return mock data when API is not running (dev/demo mode)
    return { heals: MOCK_HEALS, total: MOCK_HEALS.length }
  }
}

export async function fetchHealDetail(runId) {
  try {
    const res = await fetch(`${BASE}/heal/${runId}`)
    if (!res.ok) throw new Error('Not found')
    return res.json()
  } catch {
    return MOCK_HEALS.find(h => h.run_id === runId) || null
  }
}

// ── Mock data for standalone demo ──────────────────────────────────────
const now = Date.now()
const ago = (m) => new Date(now - m * 60000).toISOString()

export const MOCK_HEALS = [
  {
    run_id: 'a1b2c3d4',
    status: 'healed',
    failure_type: 'ui_change',
    test_name: 'should submit login form',
    test_file: 'tests/e2e/auth/login.spec.ts',
    framework: 'playwright',
    confidence: 0.94,
    selector_before: '#login-btn',
    selector_after: '[data-testid="submit-login"]',
    jira_ticket: 'QA-1042',
    pr_url: 'https://github.com/org/repo/pull/381',
    commit_sha: 'f3a9c12',
    time_saved_minutes: 35,
    retries: 1,
    error: null,
    timestamp: ago(3),
  },
  {
    run_id: 'b2c3d4e5',
    status: 'healed',
    failure_type: 'ui_change',
    test_name: 'checkout flow — apply coupon',
    test_file: 'tests/e2e/checkout/coupon.spec.ts',
    framework: 'playwright',
    confidence: 0.88,
    selector_before: '.coupon-input input',
    selector_after: '[aria-label="Coupon code"]',
    jira_ticket: 'QA-1041',
    pr_url: 'https://github.com/org/repo/pull/380',
    commit_sha: 'e1b8f44',
    time_saved_minutes: 42,
    retries: 1,
    error: null,
    timestamp: ago(47),
  },
  {
    run_id: 'c3d4e5f6',
    status: 'failed',
    failure_type: 'real_bug',
    test_name: 'payment total should include tax',
    test_file: 'tests/e2e/payment/total.spec.ts',
    framework: 'selenium',
    confidence: null,
    selector_before: null,
    selector_after: null,
    jira_ticket: 'QA-1040',
    pr_url: null,
    commit_sha: null,
    time_saved_minutes: 0,
    retries: 0,
    error: 'Real regression detected — Jira bug filed',
    timestamp: ago(92),
  },
  {
    run_id: 'd4e5f6g7',
    status: 'needs_review',
    failure_type: 'ui_change',
    test_name: 'user profile — update avatar',
    test_file: 'tests/e2e/profile/avatar.spec.ts',
    framework: 'playwright',
    confidence: 0.61,
    selector_before: '.avatar-upload',
    selector_after: '[data-testid="avatar-dropzone"]',
    jira_ticket: null,
    pr_url: 'https://github.com/org/repo/pull/379',
    commit_sha: 'c7d2a99',
    time_saved_minutes: 0,
    retries: 2,
    error: 'Confidence below threshold — routed for human review',
    timestamp: ago(130),
  },
  {
    run_id: 'e5f6g7h8',
    status: 'quarantined',
    failure_type: 'flaky',
    test_name: 'dashboard loads within 2s',
    test_file: 'tests/e2e/dashboard/perf.spec.ts',
    framework: 'playwright',
    confidence: null,
    selector_before: null,
    selector_after: null,
    jira_ticket: 'QA-1039',
    pr_url: null,
    commit_sha: null,
    time_saved_minutes: 0,
    retries: 0,
    error: 'Network timeout — test quarantined',
    timestamp: ago(205),
  },
  {
    run_id: 'f6g7h8i9',
    status: 'healed',
    failure_type: 'ui_change',
    test_name: 'search — filter by category',
    test_file: 'tests/e2e/search/filters.spec.ts',
    framework: 'selenium',
    confidence: 0.97,
    selector_before: 'select[name="category"]',
    selector_after: '[data-testid="category-filter"]',
    jira_ticket: 'QA-1038',
    pr_url: 'https://github.com/org/repo/pull/378',
    commit_sha: 'b9e3f11',
    time_saved_minutes: 28,
    retries: 1,
    error: null,
    timestamp: ago(310),
  },
  {
    run_id: 'g7h8i9j0',
    status: 'healed',
    failure_type: 'ui_change',
    test_name: 'notifications — mark all read',
    test_file: 'tests/e2e/notifications/bulk.spec.ts',
    framework: 'playwright',
    confidence: 0.91,
    selector_before: '.mark-all-read',
    selector_after: '[aria-label="Mark all as read"]',
    jira_ticket: 'QA-1037',
    pr_url: 'https://github.com/org/repo/pull/377',
    commit_sha: 'a5c1d88',
    time_saved_minutes: 31,
    retries: 1,
    error: null,
    timestamp: ago(480),
  },
]
