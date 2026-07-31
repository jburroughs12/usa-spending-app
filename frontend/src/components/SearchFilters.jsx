import { useState, useEffect } from 'react';
import { getReferenceData } from '../api/client';

export default function SearchFilters({ onSearch, loading }) {
  const [refData, setRefData] = useState(null);
  const [agency, setAgency] = useState('');
  const [psc, setPsc] = useState('');
  const [recipient, setRecipient] = useState('');
  const [setAside, setSetAside] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    getReferenceData().then(setRefData).catch(console.error);
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    onSearch({ agency, psc, recipient, setAside, startDate, endDate });
  }

  function handleReset() {
    setAgency('');
    setPsc('');
    setRecipient('');
    setSetAside('');
    setStartDate('');
    setEndDate('');
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
