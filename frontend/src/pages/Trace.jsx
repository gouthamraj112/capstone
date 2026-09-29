import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Check, ChevronRight, Radio, Clock, Cpu } from 'lucide-react'
import { getTrace } from '../services/api'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { useLanguage } from '../utils/i18n'

export default function Trace() {
  const location = useLocation()
  const { t } = useLanguage()
  const [id, setId] = useState(location.state?.traceId || '')
  const [trace, setTrace] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expandedAgent, setExpandedAgent] = useState(null)

  useEffect(() => {
    if (!id) return
    let active = true
    setLoading(true)
    setError('')
    getTrace(id).then(value => { if (active) setTrace(value) })
      .catch(() => { if (active) setError(t('traceNotFound', 'Trace not found. Run a query in the AI Assistant to create one.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id, t])

  const totalMs = trace?.agents?.reduce((s, a) => s + (a.execution_ms || 0), 0) || 0

  return <>
    <header className="page-header">
      <div>
        <div className="eyebrow">{t('traceEyebrow', 'WORKSPACE · OBSERVABILITY')}</div>
        <h1>{t('traceHeading', 'Agent Trace')}</h1>
        <p>{t('traceSub', 'Inspect the structured handoffs and evidence behind assistant responses.')}</p>
      </div>
      {trace && (
        <div style={{ display: 'flex', gap: 10 }}>
          <span className="mini-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Cpu size={12} /> {trace.agents?.length || 0} AGENTS
          </span>
          <span className="mini-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Clock size={12} /> {totalMs} MS
          </span>
        </div>
      )}
    </header>
    <section className="panel trace-panel">
      <div className="panel-heading">
        <div>
          <h2>{t('executionPipeline', 'Execution pipeline')}</h2>
          <p>{trace ? `${t('question', 'Question')}: "${trace.question}"` : t('runAssistantQuery', 'Run an assistant query to view its agent execution.')}</p>
        </div>
        {trace && <span className="trace-id">TRACE {trace.trace_id?.slice(-8)}</span>}
      </div>
      {loading ? (
        <LoadingState label={t('loadingTrace', 'Loading agent trace…')} />
      ) : error ? (
        <ErrorState message={error} />
      ) : trace?.agents?.length ? (
        <div className="trace-flow">
          {trace.agents.map((agent, index) => (
            <article
              className="trace-agent"
              key={`${agent.source_agent}-${index}`}
              style={{
                borderColor: expandedAgent === index ? 'rgba(34,211,238,0.3)' : undefined,
                boxShadow: expandedAgent === index ? '0 0 20px rgba(34,211,238,0.05)' : undefined,
              }}
            >
              <div
                className="trace-step"
                style={{ cursor: 'pointer' }}
                onClick={() => setExpandedAgent(expandedAgent === index ? null : index)}
              >
                <div className="step-number">{String(index + 1).padStart(2, '0')}</div>
                <div className="trace-step-main">
                  <div className="trace-title">
                    {agent.source_agent?.replaceAll('_', ' ') || agent.task}
                    <span className={agent.status === 'failed' ? 'severity high' : 'complete'}>
                      {agent.status === 'failed' ? 'failed' : <><Check size={13} /> {t('completed', 'completed')}</>}
                    </span>
                  </div>
                  <small>
                    {agent.task} · {agent.execution_ms} ms · {t('confidence', 'confidence')} {Math.round((agent.confidence || 0) * 100)}%
                    {/* Progress bar for relative timing */}
                    <span style={{
                      display: 'inline-block',
                      width: 60,
                      height: 3,
                      background: 'rgba(255,255,255,0.06)',
                      borderRadius: 2,
                      marginLeft: 10,
                      verticalAlign: 'middle',
                      overflow: 'hidden'
                    }}>
                      <span style={{
                        display: 'block',
                        height: '100%',
                        width: `${totalMs ? Math.max(8, (agent.execution_ms / totalMs) * 100) : 0}%`,
                        background: 'var(--accent-cyan)',
                        borderRadius: 2,
                        transition: 'width 0.5s ease',
                      }} />
                    </span>
                  </small>
                </div>
                <ChevronRight
                  size={17}
                  style={{
                    transition: 'transform 0.2s',
                    transform: expandedAgent === index ? 'rotate(90deg)' : 'none',
                    color: 'var(--text-dim)',
                  }}
                />
              </div>
              {expandedAgent === index && (
                <div style={{ borderTop: '1px solid var(--border-subtle)', padding: '10px 16px' }}>
                  <pre>{JSON.stringify({ input: trace.question, output: agent.data, evidence: agent.evidence }, null, 2)}</pre>
                </div>
              )}
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Radio size={28} />
          <b>{t('noTraceSelected', 'No agent trace selected')}</b>
          <span>{t('askToCreateTrace', 'Ask a question in AI Assistant. The trace will be saved to MongoDB.')}</span>
        </div>
      )}
    </section>
    <div className="method-note">{t('traceNote', 'Trace records include agent, task, execution time, structured output, evidence, and confidence. MongoDB must be running for retrieval.')}</div>
  </>
}
