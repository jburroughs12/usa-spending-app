import { useState, useEffect } from 'react';
import { getReferenceData } from '../api/client';

export default function SolicitationFilters({ onSearch, loading }) {
  const [refData, setRefData] = useState(null);
  const [naicsCodes, setNaicsCodes] = useState([]);
  const [setAside, setSetAside] = useState('');
  const [keyword, setKeyword] = useState('');
  const [postedFrom, setPostedFrom] = useState('');
  const [postedTo, setPostedTo] = useState('');
  const [activeOnly, setActiveOnly] = useState(true);

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
      naics: naicsCodes.length ? naicsCodes.join(',') : undefined,
      setAside: setAside || undefined,
      keyword: keyword || undefined,
      postedFrom: postedFrom || undefined,
      postedTo: postedTo || undefined,
      activeOnly,
    });
  }

  function handleReset() {
    setNaicsCodes([]);
    setSetAside('');
    setKeyword('');
    setPostedFrom('');
    setPostedTo('');
    setActiveOnly(true);
    onSearch({ activeOnly: true });
  }

  return (
    <form onSubmit={handleSubmit} className="filters">
      <h2>Solicitation Filters</h2>

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
        Set-Aside Type
        <select value={setAside} onChange={e => setSetAside(e.target.value)}>
          <option value="">Any Set-Aside</option>
          {refData?.set_aside_types.map(s => (
            <option key={s.code} value={s.code}>{s.code} — {s.name}</option>
          ))}
        </select>
      </label>

      <label>
        Keyword
        <input
          type="text"
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          placeholder="e.g. hardware, PPE"
        />
      </label>

      <label>
        Posted From
        <input type="date" value={postedFrom} onChange={e => setPostedFrom(e.target.value)} />
      </label>

      <label>
        Posted To
        <input type="date" value={postedTo} onChange={e => setPostedTo(e.target.value)} />
      </label>

      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={activeOnly}
          onChange={e => setActiveOnly(e.target.checked)}
        />
        Active only
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
