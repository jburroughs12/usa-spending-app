import { useState, useEffect } from 'react';
import { getSpendingSummary } from '../api/client';

function formatDollars(amount) {
  if (amount == null) return '$0';
  const n = Number(amount);
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
}

export default function SpendingSummary({ filters }) {
  const [byAgency, setByAgency] = useState(null);
  const [byPsc, setByPsc] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getSpendingSummary({ groupBy: 'awarding_agency', ...filters }),
      getSpendingSummary({ groupBy: 'psc', ...filters }),
    ])
      .then(([agencyData, pscData]) => {
        setByAgency(agencyData.results || []);
        setByPsc(pscData.results || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filters.agency, filters.psc, filters.startDate, filters.endDate]);

  if (loading) return <div className="summary-loading">Loading spending summary...</div>;
  if (!byAgency && !byPsc) return null;

  const totalSpend = (byAgency || []).reduce((sum, r) => sum + (r.amount || 0), 0);

  return (
    <div className="summary-cards">
      <div className="card total">
        <div className="card-label">Total Spending (Current FY)</div>
        <div className="card-value">{formatDollars(totalSpend)}</div>
      </div>

      <div className="card">
        <div className="card-label">Top Agencies</div>
        <ul>
          {(byAgency || []).slice(0, 5).map((r, i) => (
            <li key={i}>
              <span className="agency-name">{r.name}</span>
              <span className="agency-amount">{formatDollars(r.amount)}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <div className="card-label">Top Product Categories</div>
        <ul>
          {(byPsc || []).slice(0, 5).map((r, i) => (
            <li key={i}>
              <span className="psc-name">{r.name || r.code}</span>
              <span className="psc-amount">{formatDollars(r.amount)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
