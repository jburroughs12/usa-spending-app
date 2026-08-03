import { useState, useCallback, useEffect } from 'react';
import SearchFilters from './components/SearchFilters';
import ResultsTable from './components/ResultsTable';
import SpendingSummary from './components/SpendingSummary';
import BookmarkedContracts from './components/BookmarkedContracts';
import SolicitationFilters from './components/SolicitationFilters';
import SolicitationResults from './components/SolicitationResults';
import useBookmarks from './hooks/useBookmarks';
import { searchAwards, getSolicitations } from './api/client';
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

  const [solicitations, setSolicitations] = useState(null);
  const [solicitationsLoading, setSolicitationsLoading] = useState(false);
  const [solicitationsError, setSolicitationsError] = useState(null);
  const [solicitationsLoaded, setSolicitationsLoaded] = useState(false);

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

  const doSolicitationsSearch = useCallback(async (params) => {
    setSolicitationsLoading(true);
    setSolicitationsError(null);
    try {
      const data = await getSolicitations({ activeOnly: true, ...params, limit: 50 });
      setSolicitations(data.results);
    } catch (err) {
      setSolicitationsError(err.message);
      setSolicitations(null);
    } finally {
      setSolicitationsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === 'solicitations' && !solicitationsLoaded) {
      setSolicitationsLoaded(true);
      doSolicitationsSearch({});
    }
  }, [tab, solicitationsLoaded, doSolicitationsSearch]);

  return (
    <div className="app">
      <header>
        <div className="header-row">
          <div>
            <h1>Federal <span>Spending</span> Search</h1>
            <p className="subtitle">Federal Contract Search &amp; Intelligence</p>
          </div>
          <div className="tabs">
            <button
              className={`tab ${tab === 'search' ? 'active' : ''}`}
              onClick={() => setTab('search')}
            >
              Awarded Contracts
            </button>
            <button
              className={`tab ${tab === 'solicitations' ? 'active' : ''}`}
              onClick={() => setTab('solicitations')}
            >
              Solicitations
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

        {tab === 'solicitations' && (
          <aside>
            <SolicitationFilters onSearch={doSolicitationsSearch} loading={solicitationsLoading} />
          </aside>
        )}

        <main>
          {tab === 'search' && (
            <>
              <SpendingSummary filters={filters} />

              {error && <div className="error">{error}</div>}

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
                  selectedAward={selectedAward}
                  onCloseDetail={() => setSelectedAward(null)}
                />
              )}

              {results === null && !loading && (
                <div className="placeholder">
                  <p>Select filters and click <strong>Search</strong> to find federal contract awards.</p>
                  <p>Leave filters blank to search across all agencies and product/service codes, or narrow by agency, PSC code, vendor, set-aside type, or upcoming expiration window.</p>
                </div>
              )}
            </>
          )}

          {tab === 'solicitations' && (
            <SolicitationResults
              data={solicitations}
              loading={solicitationsLoading}
              error={solicitationsError}
            />
          )}

          {tab === 'bookmarks' && (
            <BookmarkedContracts
              bookmarks={bookmarks}
              onToggleBookmark={toggle}
              onClear={clear}
              selectedPiid={selectedPiid}
              onSelectContract={selectContract}
              selectedAward={selectedAward}
              onCloseDetail={() => setSelectedAward(null)}
            />
          )}
        </main>
      </div>
    </div>
  );
}
