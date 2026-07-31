import { exportToCsv } from '../api/client';

function formatDollars(amount) {
  if (amount == null) return 'N/A';
  const n = Number(amount);
  if (isNaN(n)) return 'N/A';
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const end = new Date(dateStr);
  const now = new Date();
  return Math.ceil((end - now) / (1000 * 60 * 60 * 24));
}

export default function ResultsTable({ data, hasNext, page, onPageChange, onToggleBookmark, isBookmarked, selectedPiid, onSelectContract }) {
  if (!data) return null;

  if (data.length === 0) {
    return <div className="no-results">No contracts found matching your filters.</div>;
  }

  return (
    <div className="results">
      <div className="results-header">
        <span>Showing {data.length} contracts{hasNext ? ' (more available)' : ''}</span>
        <div className="results-actions">
          <button className="secondary" onClick={() => exportToCsv(data)}>Export CSV</button>
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Prev</button>
            <span>Page {page}</span>
            <button disabled={!hasNext} onClick={() => onPageChange(page + 1)}>Next</button>
          </div>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Recipient</th>
              <th>Agency</th>
              <th>Sub-Agency</th>
              <th>Amount</th>
              <th>Description</th>
              <th>Set-Aside</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th>Days Left</th>
              <th>Award ID</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => {
              const days = daysUntil(row['End Date']);
              const expiring = days != null && days > 0 && days <= 180;
              const saved = isBookmarked?.(row['Award ID']);
              return (
                <tr
                  key={row['Award ID'] || i}
                  className={[
                    expiring ? 'expiring' : '',
                    'clickable',
                    selectedPiid === row['Award ID'] ? 'selected' : '',
                  ].filter(Boolean).join(' ')}
                  onClick={() => onSelectContract?.(row)}
                >
                  <td>
                    <button
                      className={`bookmark-btn ${saved ? 'bookmarked' : ''}`}
                      onClick={(e) => { e.stopPropagation(); onToggleBookmark?.(row); }}
                      title={saved ? 'Remove bookmark' : 'Bookmark this contract'}
                    >
                      {saved ? '\u2605' : '\u2606'}
                    </button>
                  </td>
                  <td className="recipient">{row['Recipient Name'] || '\u2014'}</td>
                  <td>{row['Awarding Agency'] || '\u2014'}</td>
                  <td className="office">{row['Awarding Sub Agency'] || '\u2014'}</td>
                  <td className="amount">{formatDollars(row['Award Amount'])}</td>
                  <td className="description">{row['Description']?.slice(0, 120) || '\u2014'}</td>
                  <td>{row['Type of Set Aside'] || '\u2014'}</td>
                  <td>{row['Start Date'] || '\u2014'}</td>
                  <td>{row['End Date'] || '\u2014'}</td>
                  <td className={expiring ? 'days-warn' : ''}>
                    {days != null ? (days > 0 ? days : 'Expired') : '\u2014'}
                  </td>
                  <td className="award-id">{row['Award ID'] || '\u2014'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
