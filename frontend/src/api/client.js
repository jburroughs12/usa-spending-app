const BASE = '/api';

export async function searchAwards(params) {
  const qs = new URLSearchParams();
  if (params.agency) qs.set('agency', params.agency);
  if (params.psc) qs.set('psc', params.psc);
  if (params.recipient) qs.set('recipient', params.recipient);
  if (params.startDate) qs.set('start_date', params.startDate);
  if (params.endDate) qs.set('end_date', params.endDate);
  if (params.setAside) qs.set('set_aside', params.setAside);
  if (params.sort) qs.set('sort', params.sort);
  if (params.order) qs.set('order', params.order);
  if (params.page) qs.set('page', params.page);
  if (params.limit) qs.set('limit', params.limit);

  const res = await fetch(`${BASE}/search?${qs}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getSpendingSummary(params) {
  const qs = new URLSearchParams();
  if (params.groupBy) qs.set('group_by', params.groupBy);
  if (params.agency) qs.set('agency', params.agency);
  if (params.psc) qs.set('psc', params.psc);
  if (params.startDate) qs.set('start_date', params.startDate);
  if (params.endDate) qs.set('end_date', params.endDate);

  const res = await fetch(`${BASE}/spending-summary?${qs}`);
  if (!res.ok) throw new Error(`Summary failed: ${res.status}`);
  return res.json();
}

export async function getReferenceData() {
  const res = await fetch(`${BASE}/reference-data`);
  if (!res.ok) throw new Error(`Reference data failed: ${res.status}`);
  return res.json();
}

export function exportToCsv(data, filename = 'bbs-contracts.csv') {
  if (!data || data.length === 0) return;

  const columns = [
    'Award ID', 'Recipient Name', 'Awarding Agency', 'Awarding Sub Agency',
    'Awarding Office Name', 'Award Amount', 'Description', 'Type of Set Aside',
    'Start Date', 'End Date', 'Contract Award Type', 'Place of Performance State Code',
    'Recipient UEI',
  ];

  const escape = (val) => {
    if (val == null) return '';
    const s = String(val);
    if (s.includes(',') || s.includes('"') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const header = columns.map(escape).join(',');
  const rows = data.map(row => columns.map(col => escape(row[col])).join(','));
  const csv = [header, ...rows].join('\n');

  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function getAwardDetail(internalId) {
  const res = await fetch(`${BASE}/award-detail?internal_id=${encodeURIComponent(internalId)}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    const body = await res.json().catch(() => null);
    const detail = body?.detail || `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json();
}

// On-demand only: looks up the contracting officer via SAM.gov, which has a
// much stricter rate limit than USASpending.gov. Callers should trigger this
// explicitly rather than automatically on every contract view.
export async function getContractingOfficer(piid) {
  const res = await fetch(`${BASE}/contract-detail?piid=${encodeURIComponent(piid)}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    const body = await res.json().catch(() => null);
    const detail = body?.detail || `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json();
}
