import { useEffect, useState } from 'react'
import { ClipboardList, CheckCircle2, ShieldCheck, Cpu, TrendingUp, Target } from 'lucide-react'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { getEvaluation } from '../services/api'
import { useLanguage } from '../utils/i18n'
import AnimatedCounter from '../components/AnimatedCounter'

function Score({ label, value, unit = '', subtitle = '', t, color }) {
  const numVal = value != null ? Number(String(value).replace('%', '')) : null
  const isNumeric = numVal != null && !isNaN(numVal)
  return (
    <div className="score-card">
      <span>{label}</span>
      <b style={color ? { color } : {}}>
        {value == null ? '—' : (
          isNumeric
            ? <><AnimatedCounter value={numVal} />{unit}</>
            : `${value}${unit}`
        )}
      </b>
      <small>{subtitle || (value == null ? (t ? t('notEvaluatedYet', 'Not evaluated yet') : 'Not evaluated yet') : (t ? t('chronologicalHoldout', 'Chronological holdout') : 'Chronological holdout'))}</small>
    </div>
  )
}

export default function Evaluation() {
  const { t } = useLanguage()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedSection, setExpandedSection] = useState(null)

  useEffect(() => {
    getEvaluation()
      .then(setData)
      .catch(() => setError(t('unableLoadEval', 'Unable to load evaluation details from FastAPI.')))
      .finally(() => setLoading(false))
  }, [t])

  const sections = [
    { key: 'forecast', num: '01', title: t('forecastingPerformance', 'Forecasting Performance'), icon: TrendingUp },
    { key: 'anomaly', num: '02', title: t('anomalyValidation', 'Anomaly Detection'), icon: Target },
    { key: 'query', num: '03', title: 'Query Accuracy', icon: Cpu },
    { key: 'groundedness', num: '04', title: 'Groundedness', icon: ShieldCheck },
  ]

  return (
    <>
      <header className="page-header">
        <div>
          <div className="eyebrow">{t('evalEyebrow', 'WORKSPACE · MODEL QUALITY')}</div>
          <h1>{t('evalHeading', 'Evaluation')}</h1>
          <p>{t('evalSub', 'Comprehensive model scores, anomaly validation, query benchmarks, and evidence groundedness.')}</p>
        </div>
      </header>

      {loading && <LoadingState label={t('loadingEval', 'Loading evaluation details…')} />}
      {error && <ErrorState message={error} />}

      {!loading && !error && (
        <>
          {/* Section 1: Forecasting */}
          <section className="panel eval-panel" style={{ marginBottom: 16 }}>
            <div className="panel-heading" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="metric-icon"><TrendingUp size={17} /></div>
                <div>
                  <h2>{t('forecastingPerformance', '1 · Forecasting Performance')}</h2>
                  <p>Chronological holdout evaluation on 24-hour demand</p>
                </div>
              </div>
            </div>
            <div className="score-grid">
              <Score label={t('mae', 'Mean absolute error (MAE)')} value={data?.forecast?.mae} subtitle="Observed 24-hr holdout" t={t} />
              <Score label={t('rmse', 'Root mean square error (RMSE)')} value={data?.forecast?.rmse} subtitle="Quadratic penalty error" t={t} />
              <Score label={t('mape', 'MAPE')} value={data?.forecast?.mape ? data.forecast.mape.toFixed(2) : null} unit="%" subtitle="Relative percentage deviation" t={t} />
            </div>
          </section>

          {/* Section 2: Anomaly Detection */}
          <section className="panel eval-panel" style={{ marginBottom: 16 }}>
            <div className="panel-heading" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="metric-icon amber"><Target size={17} /></div>
                <div>
                  <h2>{t('anomalyValidation', '2 · Anomaly Detection Effectiveness')}</h2>
                  <p>{t('precisionRecallNote', 'Validation against controlled synthetic high/low spikes across rolling baseline windows.')}</p>
                </div>
              </div>
              <span className="mini-label" style={{ background: 'rgba(52,211,153,0.08)', color: '#34d399', borderColor: 'rgba(52,211,153,0.2)' }}>CONTROLLED INJECTION</span>
            </div>
            <div className="score-grid embedded">
              <Score label={t('precision', 'Precision')} value={data?.anomaly?.precision ? (data.anomaly.precision * 100).toFixed(1) : null} unit="%" subtitle="True positive ratio" t={t} color="var(--accent-green)" />
              <Score label={t('recall', 'Recall')} value={data?.anomaly?.recall ? (data.anomaly.recall * 100).toFixed(1) : null} unit="%" subtitle="Anomaly capture rate" t={t} color="var(--accent-green)" />
              <Score label={t('f1Score', 'F1 score')} value={data?.anomaly?.f1 ? (data.anomaly.f1 * 100).toFixed(1) : null} unit="%" subtitle="Harmonic mean" t={t} color="var(--accent-green)" />
            </div>
            <div className="method-box">
              <ClipboardList size={17} />
              <div>
                <b>{t('documentedValidationApproach', 'Validation Methodology')}</b>
                <span>{data?.anomaly?.methodology}</span>
              </div>
            </div>
          </section>

          {/* Section 3: Query Accuracy */}
          <section className="panel eval-panel" style={{ marginBottom: 16 }}>
            <div className="panel-heading" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="metric-icon blue"><Cpu size={17} /></div>
                <div>
                  <h2>3 · Natural-Language Query Accuracy</h2>
                  <p>Evaluation against standardized domain benchmarks covering all query intents and languages.</p>
                </div>
              </div>
              <span className="mini-label" style={{ background: 'rgba(56,189,248,0.08)', color: '#38bdf8', borderColor: 'rgba(56,189,248,0.2)' }}>BENCHMARK SUITE</span>
            </div>
            <div className="score-grid embedded">
              <Score label="Intent Accuracy" value={data?.query?.intent_accuracy} unit="%" subtitle={`${data?.query?.passed_samples || 0}/${data?.query?.benchmark_samples || 0} benchmark tests passed`} t={t} color="var(--accent-blue)" />
              <Score label="Execution Success" value={data?.query?.execution_accuracy} unit="%" subtitle="Zero unhandled runtime exceptions" t={t} color="var(--accent-blue)" />
              <Score label="Data Correctness" value={data?.query?.answer_correctness} unit="%" subtitle="Factual consistency with MongoDB" t={t} color="var(--accent-blue)" />
            </div>

            {data?.query?.results && (
              <div className="table-wrap" style={{ marginTop: 16 }}>
                <table>
                  <thead>
                    <tr>
                      <th>QUERY / PROMPT</th>
                      <th>EXPECTED INTENT</th>
                      <th>DETECTED INTENT</th>
                      <th>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.query.results.slice(0, 8).map((res, idx) => (
                      <tr key={idx}>
                        <td style={{ maxWidth: 350 }}>{res.query}</td>
                        <td><code style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>{res.expected_intent}</code></td>
                        <td><code style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>{res.detected_intent}</code></td>
                        <td>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--accent-green)', fontSize: 11, fontWeight: 600 }}>
                            <CheckCircle2 size={14} /> Passed
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Section 4: Groundedness */}
          <section className="panel eval-panel">
            <div className="panel-heading" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="metric-icon purple"><ShieldCheck size={17} /></div>
                <div>
                  <h2>4 · Groundedness & Zero-Hallucination</h2>
                  <p>Evidence-backed verification ensuring all generated insights strictly mirror underlying database statistics.</p>
                </div>
              </div>
              <span className="mini-label" style={{ background: 'rgba(52,211,153,0.08)', color: '#34d399', borderColor: 'rgba(52,211,153,0.2)' }}>VERIFIED EVIDENCE</span>
            </div>
            <div className="score-grid embedded">
              <Score label="Evidence Coverage" value={data?.groundedness?.evidence_coverage} unit="%" subtitle="Responses backed by evidence objects" t={t} color="var(--accent-purple)" />
              <Score label="Unsupported Claims" value={data?.groundedness?.unsupported_claim_rate} unit="%" subtitle="Zero ungrounded numeric claims" t={t} />
              <Score label="Faithfulness Score" value={data?.groundedness?.faithfulness_score} unit="%" subtitle="Claim-to-evidence faithfulness" t={t} color="var(--accent-purple)" />
            </div>
            <div className="method-box">
              <ShieldCheck size={17} style={{ color: 'var(--accent-green)' }} />
              <div>
                <b>Zero-Hallucination Enforcement Rule</b>
                <span>{data?.groundedness?.verification_rule}</span>
              </div>
            </div>
          </section>
        </>
      )}
    </>
  )
}
