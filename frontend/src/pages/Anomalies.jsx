import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle, Filter, Info, Search, X } from 'lucide-react'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { getAnomalies, getAnomalyDetail } from '../services/api'
import { formatTimestamp } from '../utils/dates'
import { useLanguage } from '../utils/i18n'
import AnimatedCounter from '../components/AnimatedCounter'

export default function Anomalies() {
  const { t } = useLanguage()
  const [data, setData] = useState([])
  const [method, setMethod] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedAnomaly, setSelectedAnomaly] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [severityFilter, setSeverityFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    getAnomalies(100)
      .then(result => {
        setData(result.items || [])
        setMethod(result.method || '')
      })
      .catch(() => setError('Unable to load anomaly records. Check FastAPI and MongoDB.'))
      .finally(() => setLoading(false))
  }, [])

  const handleSelectAnomaly = async (id) => {
    if (!id) return
    setLoadingDetail(true)
    try {
      const detail = await getAnomalyDetail(id)
      setSelectedAnomaly(detail)
    } catch (e) {
      console.error('Failed to load anomaly detail:', e)
    } finally {
      setLoadingDetail(false)
    }
  }

  const high = data.filter(item => item.severity === 'high').length
  const medium = data.filter(item => item.severity === 'medium').length
  const low = data.filter(item => item.severity === 'low').length

  const filtered = data.filter(item => {
    if (severityFilter !== 'all' && item.severity !== severityFilter) return false
    if (searchTerm && !item.reason?.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !formatTimestamp(item.timestamp).includes(searchTerm)) return false
    return true
  })

  return (
    <>
      <header className="page-header">
        <div>
          <div className="eyebrow">{t('anomaliesEyebrow', 'WORKSPACE · MONITORING')}</div>
          <h1>{t('anomaliesHeading', 'Anomaly Detection')}</h1>
          <p>{t('anomaliesSub', 'Unusual consumption identified against a robust rolling baseline.')}</p>
        </div>
        <div className="segmented">
          {['all', 'high', 'medium', 'low'].map(s => (
            <button
              key={s}
              className={severityFilter === s ? 'selected' : ''}
              onClick={() => setSeverityFilter(s)}
            >
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </header>

      {loading && <LoadingState label="Loading anomaly records…" />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <>
          <div className="metric-grid anomaly-metrics">
            <div className="small-kpi metric-card">
              <span>{t('totalDetected', 'Total detected')}</span>
              <b><AnimatedCounter value={data.length} decimals={0} /></b>
            </div>
            <div className="small-kpi metric-card">
              <span>{t('highSeverity', 'High severity')}</span>
              <b className="red-text"><AnimatedCounter value={high} decimals={0} /></b>
            </div>
            <div className="small-kpi metric-card">
              <span>{t('mediumSeverity', 'Medium severity')}</span>
              <b className="amber-text"><AnimatedCounter value={medium} decimals={0} /></b>
            </div>
            <div className="small-kpi metric-card">
              <span>{t('detectionMethod', 'Detection method')}</span>
              <b className="method-text">Rolling MAD</b>
            </div>
          </div>

          <section className="panel" style={{ padding: '18px 20px' }}>
            <div className="panel-heading">
              <div>
                <h2>{t('detectedAnomalies', 'Detected periods')} · {filtered.length}</h2>
                <p>{method || 'Anomalies are calculated from actual ingested readings.'}</p>
              </div>
              <div style={{ position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
                <input
                  type="text"
                  placeholder="Search anomalies…"
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '7px 10px 7px 32px',
                    color: 'var(--text-primary)',
                    fontSize: '11px',
                    width: '200px',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={e => e.target.style.borderColor = 'rgba(34,211,238,0.3)'}
                  onBlur={e => e.target.style.borderColor = 'var(--border-default)'}
                />
              </div>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{t('timestamp', 'TIMESTAMP')}</th>
                    <th>{t('actual', 'ACTUAL')}</th>
                    <th>{t('expected', 'EXPECTED')}</th>
                    <th>{t('deviation', 'DEVIATION')}</th>
                    <th>{t('score', 'SCORE')}</th>
                    <th>{t('severity', 'SEVERITY')}</th>
                    <th>{t('reason', 'REASON')}</th>
                    <th>DETAIL</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(item => (
                    <tr
                      key={item.id || item.timestamp}
                      style={{ cursor: item.id ? 'pointer' : 'default' }}
                      onClick={() => item.id && handleSelectAnomaly(item.id)}
                    >
                      <td>{formatTimestamp(item.timestamp)}</td>
                      <td>{Number(item.actual_value).toFixed(2)} kW</td>
                      <td>{Number(item.expected_value).toFixed(2)} kW</td>
                      <td className={item.deviation > 0 ? 'red-text' : 'blue-text'}>
                        {item.deviation > 0 ? '+' : ''}{Number(item.deviation).toFixed(2)} kW
                      </td>
                      <td>{Number(item.anomaly_score).toFixed(2)}</td>
                      <td><span className={`severity ${item.severity}`}>{item.severity}</span></td>
                      <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.reason}</td>
                      <td>
                        {item.id && (
                          <button
                            type="button"
                            className="btn-inspect"
                            onClick={e => { e.stopPropagation(); handleSelectAnomaly(item.id) }}
                          >
                            Inspect
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {!filtered.length && (
                <div className="empty-state">
                  <AlertTriangle size={26} />
                  <b>{data.length ? 'No matching anomalies' : 'No anomaly records'}</b>
                  <span>{data.length ? 'Try adjusting the filter or search term.' : 'Ingest the dataset to run anomaly detection.'}</span>
                </div>
              )}
            </div>
          </section>

          {selectedAnomaly && (
            <div className="anomaly-modal-backdrop" onClick={() => setSelectedAnomaly(null)}>
              <div className="anomaly-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                  <div className="modal-title">
                    <Info size={18} />
                    <b>Anomaly Detail · {formatTimestamp(selectedAnomaly.timestamp)}</b>
                  </div>
                  <button className="btn-close" onClick={() => setSelectedAnomaly(null)}>
                    <X size={16} />
                  </button>
                </div>
                <div className="modal-body">
                  <div className="modal-metrics">
                    <div><span>Observed Power:</span> <b>{Number(selectedAnomaly.actual_value).toFixed(3)} kW</b></div>
                    <div><span>Expected Baseline:</span> <b>{Number(selectedAnomaly.expected_value).toFixed(3)} kW</b></div>
                    <div><span>Deviation:</span> <b className={selectedAnomaly.deviation > 0 ? 'red-text' : 'blue-text'}>{selectedAnomaly.deviation > 0 ? '+' : ''}{Number(selectedAnomaly.deviation).toFixed(3)} kW</b></div>
                    <div><span>Robust Score:</span> <b>{Number(selectedAnomaly.anomaly_score).toFixed(3)}</b></div>
                    <div><span>Severity Level:</span> <span className={`severity ${selectedAnomaly.severity}`}>{selectedAnomaly.severity}</span></div>
                    <div><span>ID:</span> <code>{selectedAnomaly.id}</code></div>
                  </div>
                  <p className="modal-reason">{selectedAnomaly.reason}</p>
                </div>
              </div>
            </div>
          )}

          <p className="method-note">{method}. The source data has no ground-truth event labels.</p>
        </>
      )}
    </>
  )
}
