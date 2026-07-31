import { useState, useEffect } from 'react';
import { getReferenceData } from '../api/client';

const EXPIRING_PRESETS = [
  { label: 'Any time', value: '' },
  { label: 'Next 30 days', value: '30' },
  { label: 'Next 90 days', value: '90' },
  { label: 'Next 180 days', value: '180' },
  { label: 'Next 365 days', value: '365' },
];

export default function SearchFilters({ onSearch, loading }) {
  const [refData, setRefData] = useState(null);
  const [agency, setAgency] = useState('');
  const [psc, setPsc] = useState('');
  const [naicsCodes, setNaicsCodes] = useState([]);
  const [recipient, setRecipient] = useState('');
  const [setAside, setSetAside] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [expiringWithinDays, setExpiringWithinDays] = useState('');

  useEffect(() => {
    getReferenceData().then(setRefData).catch(console.error);
  }, []);

  function toggleNaics(code) {
    setNaicsCodes(prev =>
      prev.includes(code) ? prev.filter(c => c !== code) : [...prev, code]
    );
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSearch({
      agency,
      psc,
      naics: naicsCodes.length ? naicsCodes.join(',') : undefined,
      recipient,
      setAside,
      startDate,
      endDate,
      expiringWithinDays: expiringWithinDays || undefined,
    });
  }

  function handleReset() {
    setAgency('');
    setPsc('');
    setNaicsCodes([]);
    setRecipient('');
    setSetAside('');
    setStartDate('');
    setEndDate('');
    setExpiringWithinDays('');
    onSearch({});
  }

  return (
    <form onSubmit={handleSubmit} className="filters">
      <h2>Search Filters</h2>

      <label>
        Agency
        <select value={agency} onChange={e => setAgency(e.target.value)}>
          <option value="">All Agencies</option>
          {refData?.agencies.map(a => (
            <option key={a.name} value={a.name}>
              {a.abbreviation ? `${a.abbreviation} — ${a.name}` : a.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        NAICS Codes
        <span className="filter-hint">Blank = default Grainger-relevant set</span>
      </label>
      <div className="naics-checklist">
        {refData?.naics_codes.map(n => (
          <label key={n.code} className="naics-checkbox">
            <input
              type="checkbox"
              checked={naicsCodes.includes(n.code)}
              onChange={() => toggleNaics(n.code)}
            />
            <span>{n.code} — {n.description}</span>
          </label>
        ))}
      </div>

      <label>
        Product/Service Code (PSC)
        <input
          type="text"
          value={psc}
          onChange={e => setPsc(e.target.value)}
          placeholder="e.g. 6515, 8415 (blank = all)"
        />
      </label>

      <label>
        Vendor / Recipient Name
        <input
          type="text"
          value={recipient}
          onChange={e => setRecipient(e.target.value)}
          placeholder="e.g. Acme Corp"
        />
      </label>

      <label>
        Set-Aside Type
        <select value={setAside} onChange={e => setSetAside(e.target.value)}>
          <option value="">Any Set-Aside</option>
          {refData?.set_aside_types.map(s => (
            <option key={s.code} value={s.code}>{s.code} — {s.name}</option>
          ))}
        </select>
      </label>

      <label>
        Expiring Within
        <select value={expiringWithinDays} onChange={e => setExpiringWithinDays(e.target.value)}>
          {EXPIRING_PRESETS.map(p => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
      </label>

      <label>
        Start Date
        <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
      </label>

      <label>
        End Date
        <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
      </label>

      <div className="filter-actions">
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
        <button type="button" onClick={handleReset} className="secondary">
          Reset
        </button>
      </div>
    </form>
  );
}
