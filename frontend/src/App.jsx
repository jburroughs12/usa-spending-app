import { useState, useCallback } from 'react';
import SearchFilters from './components/SearchFilters';
import ResultsTable from './components/ResultsTable';
import SpendingSummary from './components/SpendingSummary';
import BookmarkedContracts from './components/BookmarkedContracts';
import ContractDetail from './components/ContractDetail';
import useBookmarks from './hooks/useBookmarks';
import { searchAwards } from './api/client';
import './App.css';

export default function App() {
  const [results, setResults] = useState(null);
  const [hasNext, setHasNext] = useState(false);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({});
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('search');
  const [selectedAward, setSelectedAward] = useState(null);
  const selectedPiid = selectedAward?.['Award ID'] ?? null;
  const { bookmarks, toggle, isBookmarked, clear } = useBookmarks();

  function selectContract(row) {
    setSelectedAward(prev => (prev && prev['Award ID'] === row['Award ID'] ? null : row));
  }

  const doSearch = useCallback(async (params, pg = 1) => {
    setLoading(true);
    setError(null);
    try {
      const data = await searchAwards({ ...params, page: pg, limit: 50 });
      setResults(data.results);
      setHasNext(data.has_next);
      setPage(pg);
      setFilters(params);
    } catch (err) {
      setError(err.message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  function handleSearch(params) {
    setTab('search');
    doSearch(params, 1);
  }

  function handlePageChange(newPage) {
    doSearch(filters, newPage);
  }

  return (
    <div className="app">
      <header>
        <div className="header-row">
          <div>
            <h1>BLACK <span>BOX</span> SAFETY — Federal Spending</h1>
            <p className="subtitle">Service-Disabled Veteran-Owned Small Business | Federal Contract Intelligence</p>
          </div>
          <div className="tabs">
            <button
              className={`tab ${tab === 'search' ? 'active' : ''}`}
              onClick={() => setTab('search')}
            >
              Search
            </button>
            <button
              className={`tab ${tab === 'bookmarks' ? 'active' : ''}`}
              onClick={() => setTab('bookmarks')}
            >
              Bookmarked ({bookmarks.length})
            </button>
          </div>
        </div>
      </header>

      <div className="layout">
        {tab === 'search' && (
          <aside>
            <SearchFilters onSearch={handleSearch} loading={loading} />
          </aside>
        )}

        <main>
          {tab === 'search' && (
            <>
              <SpendingSummary filters={filters} />

              {error && <div className="error">{error}</div>}

              {selectedAward && (
                <ContractDetail
                  key={selectedAward['Award ID']}
                  award={selectedAward}
                  onClose={() => setSelectedAward(null)}
                />
              )}

              {results !== null && (
                <ResultsTable
                  data={results}
                  hasNext={hasNext}
                  page={page}
                  onPageChange={handlePageChange}
                  onToggleBookmark={toggle}
                  isBookmarked={isBookmarked}
                  selectedPiid={selectedPiid}
                  onSelectContract={selectContract}
                />
              )}

              {results === null && !loading && (
                <div className="placeholder">
                  <p>Select filters and click <strong>Search</strong> to find federal contracts in BBS product categories.</p>
                  <p>All results are pre-filtered to BBS's target agencies and product codes (PSCs).</p>
                </div>
              )}
            </>
          )}

          {tab === 'bookmarks' && (
            <>
              {selectedAward && (
                <ContractDetail
                  key={selectedAward['Award ID']}
                  award={selectedAward}
                  onClose={() => setSelectedAward(null)}
                />
              )}
              <BookmarkedContracts
                bookmarks={bookmarks}
                onToggleBookmark={toggle}
                onClear={clear}
                selectedPiid={selectedPiid}
                onSelectContract={selectContract}
              />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
