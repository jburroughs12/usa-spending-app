function formatDate(dateStr) {
  if (!dateStr) return '—';
  return dateStr.slice(0, 10);
}

export default function SolicitationResults({ data, loading, error, onLoad }) {
  if (loading) return <div className="summary-loading">Loading solicitations...</div>;

  if (error) {
    return (
      <div className="error">
        {error}
        <div><button className="secondary" onClick={onLoad}>Retry</button></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="placeholder">
        <p>SAM.gov's Opportunities API has a strict daily quota — as low as 10 requests/day for individual accounts not tied to a company entity registration — so solicitations aren't fetched automatically.</p>
        <p>Click below when you're ready to check for new solicitations. Once loaded, results are cached for 24 hours, so revisiting this tab or changing filters won't use up more of the quota.</p>
        <button onClick={onLoad}>Load Solicitations (SAM.gov)</button>
      </div>
    );
  }

  if (data.length === 0) {
    return <div className="no-results">No open solicitations found matching your filters.</div>;
  }

  return (
    <div className="solicitation-list">
      <div className="results-header">
        <span>Showing {data.length} solicitations</span>
      </div>

      {data.map(s => (
        <div key={s.notice_id} className="solicitation-card">
          <div className="solicitation-header">
            <div>
              <h3>
                {s.sam_url ? (
                  <a href={s.sam_url} target="_blank" rel="noreferrer">{s.title}</a>
                ) : s.title}
              </h3>
              <div className="solicitation-meta">
                {s.agency || 'Unknown agency'} · NAICS {s.naics_code || '—'} · PSC {s.psc_code || '—'}
              </div>
            </div>
            <div className="solicitation-header-right">
              <span className="set-aside-badge">{s.set_aside || 'Full/Open'}</span>
              {s.sam_url && (
                <a className="secondary" href={s.sam_url} target="_blank" rel="noreferrer">
                  View on SAM.gov
                </a>
              )}
            </div>
          </div>

          <div className="solicitation-details">
            <span><strong>Posted:</strong> {formatDate(s.posted_date)}</span>
            <span><strong>Response Due:</strong> {formatDate(s.response_deadline)}</span>
            {s.point_of_contact && <span><strong>Contact:</strong> {s.point_of_contact}</span>}
          </div>

          {s.recommended_resellers?.length > 0 && (
            <div className="reseller-recommendations">
              <strong>Best-fit resellers:</strong>
              {s.recommended_resellers.map(r => (
                <span key={r.name} className="reseller-chip" title={r.reasons.join('; ')}>
                  {r.name}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
