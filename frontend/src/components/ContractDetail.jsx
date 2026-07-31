import { useState, useEffect } from 'react';
import { getAwardDetail, getContractingOfficer } from '../api/client';

function formatDollars(amount) {
  if (amount == null) return 'N/A';
  const n = Number(amount);
  if (isNaN(n)) return 'N/A';
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function ContractDetail({ award, onClose }) {
  const piid = award?.['Award ID'];
  const internalId = award?.internal_id;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [co, setCo] = useState(null);
  const [coLoading, setCoLoading] = useState(false);
  const [coError, setCoError] = useState(null);
  const [coRequested, setCoRequested] = useState(false);

  useEffect(() => {
    if (!internalId) {
      setLoading(false);
      setError('No USASpending.gov record id available for this contract.');
      return;
    }

    setLoading(true);
    setError(null);
    getAwardDetail(internalId)
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [internalId]);

  function lookupContractingOfficer() {
    if (!piid) return;
    setCoRequested(true);
    setCoLoading(true);
    setCoError(null);
    getContractingOfficer(piid)
      .then(d => {
        setCo(d);
        setCoLoading(false);
      })
      .catch(err => {
        setCoError(err.message);
        setCoLoading(false);
      });
  }

  if (loading) {
    return (
      <div className="detail-panel">
        <div className="detail-header">
          <h3>Contract Detail</h3>
          <button className="secondary" onClick={onClose}>Close</button>
        </div>
        <div className="detail-loading">Loading USASpending.gov data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="detail-panel">
        <div className="detail-header">
          <h3>Contract Detail</h3>
          <button className="secondary" onClick={onClose}>Close</button>
        </div>
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="detail-panel">
        <div className="detail-header">
          <h3>Contract Detail</h3>
          <button className="secondary" onClick={onClose}>Close</button>
        </div>
        <div className="detail-empty">No USASpending.gov record found for {piid}</div>
      </div>
    );
  }

  return (
    <div className="detail-panel">
      <div className="detail-header">
        <h3>Contract Detail — {data.piid}</h3>
        <button className="secondary" onClick={onClose}>Close</button>
      </div>

      <div className="detail-grid">
        <section className="detail-section">
          <h4>Contracting Office</h4>
          <dl>
            <dt>Department</dt>
            <dd>{data.department_name || '—'}</dd>
            <dt>Sub-Tier Agency</dt>
            <dd>{data.subtier_name || '—'}</dd>
            <dt>Office</dt>
            <dd>{data.office_name || '—'}</dd>
          </dl>
        </section>

        <section className="detail-section">
          <h4>Contracting Personnel</h4>
          {!coRequested && (
            <>
              <p className="detail-hint">
                Contracting officer contact comes from SAM.gov, which has a strict rate limit. Look it up only when you need it.
              </p>
              <button className="secondary" onClick={lookupContractingOfficer}>
                Look up contracting officer (SAM.gov)
              </button>
            </>
          )}
          {coLoading && <div className="detail-loading">Looking up SAM.gov data...</div>}
          {coError && (
            <div className="error">
              {coError}
              <div>
                <button className="secondary" onClick={lookupContractingOfficer}>Retry</button>
              </div>
            </div>
          )}
          {co && (
            <dl>
              <dt>Created By</dt>
              <dd className="co-email">{co.created_by || '—'}</dd>
              <dt>Approved By</dt>
              <dd className="co-email">{co.approved_by || '—'}</dd>
              {co.last_modified_by && co.last_modified_by !== co.approved_by && <>
                <dt>Last Modified By</dt>
                <dd className="co-email">{co.last_modified_by}</dd>
              </>}
            </dl>
          )}
        </section>

        <section className="detail-section">
          <h4>Awardee</h4>
          <dl>
            <dt>Name</dt>
            <dd>{data.awardee_name || '—'}</dd>
            {data.awardee_parent_name && data.awardee_parent_name !== data.awardee_name && <>
              <dt>Parent</dt>
              <dd>{data.awardee_parent_name}</dd>
            </>}
            <dt>UEI</dt>
            <dd>{data.awardee_uei || '—'}</dd>
            <dt>Address</dt>
            <dd>
              {[data.awardee_address, data.awardee_city, data.awardee_state, data.awardee_zip]
                .filter(Boolean).join(', ') || '—'}
            </dd>
          </dl>
        </section>

        <section className="detail-section">
          <h4>Financials</h4>
          <dl>
            <dt>Action Obligation</dt>
            <dd className="amount">{formatDollars(data.action_obligation)}</dd>
            <dt>Base & Options Value</dt>
            <dd className="amount">{formatDollars(data.base_and_options_value)}</dd>
          </dl>
        </section>

        <section className="detail-section">
          <h4>Product / Service</h4>
          <dl>
            <dt>PSC</dt>
            <dd>{data.psc_code ? `${data.psc_code} — ${data.psc_description || ''}` : '—'}</dd>
            <dt>NAICS</dt>
            <dd>{data.naics_code ? `${data.naics_code} — ${data.naics_description || ''}` : '—'}</dd>
            {data.description && <>
              <dt>Description</dt>
              <dd>{data.description}</dd>
            </>}
          </dl>
        </section>

        <section className="detail-section">
          <h4>Competition</h4>
          <dl>
            <dt>Set-Aside</dt>
            <dd>{data.set_aside_type || '—'}</dd>
            <dt>Extent Competed</dt>
            <dd>{data.extent_competed || '—'}</dd>
            <dt>Solicitation Procedures</dt>
            <dd>{data.solicitation_procedures || '—'}</dd>
          </dl>
        </section>

        <section className="detail-section">
          <h4>Dates</h4>
          <dl>
            <dt>Signed</dt>
            <dd>{data.signed_date || '—'}</dd>
            <dt>Period of Performance</dt>
            <dd>{data.effective_date || '—'}</dd>
            <dt>Completion</dt>
            <dd>{data.completion_date || '—'}</dd>
          </dl>
        </section>

        {(data.pop_city || data.pop_state) && (
          <section className="detail-section">
            <h4>Place of Performance</h4>
            <dl>
              <dt>Location</dt>
              <dd>{[data.pop_city, data.pop_state].filter(Boolean).join(', ')}</dd>
            </dl>
          </section>
        )}
      </div>
    </div>
  );
}
