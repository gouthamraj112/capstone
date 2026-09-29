import { useState, useRef, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle, ArrowUp, Bot, BarChart2, Check, ChevronDown, ChevronRight,
  Database, ExternalLink, FileText, HelpCircle, LoaderCircle,
  Mic, MicOff, Radio, RotateCcw, Shield, Sparkles,
  Trash2, User, Volume2, VolumeX, Zap
} from 'lucide-react'
import { ask } from '../services/api'
import { useLanguage } from '../utils/i18n'
import { useVoice } from '../utils/useVoice'
import AssistantPictorial from '../components/AssistantPictorial'

const HISTORY_KEY = 'assistant_chat_history'
const MAX_HISTORY = 60

// ─── Per-message Evaluation Widget ────────────────────────────────────────────
function EvalWidget({ evaluation }) {
  const [open, setOpen] = useState(false)
  if (!evaluation) return null

  const qualityColor = {
    High: 'var(--accent-green, #34d399)',
    Medium: '#f59e0b',
    Low: '#f43f5e',
  }[evaluation.quality] || 'var(--text-muted)'

  const densityDots = { High: '●●●', Medium: '●●○', Low: '●○○' }[evaluation.evidence_density] || '○○○'

  return (
    <div className="eval-widget">
      <button
        type="button"
        className="eval-widget-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <BarChart2 size={13} />
        <span>Response Evaluation</span>
        <span className="eval-quality-badge" style={{ color: qualityColor }}>{evaluation.quality}</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>

      {open && (
        <div className="eval-widget-body">
          <div className="eval-metrics-grid">
            {[
              { label: 'Confidence', value: evaluation.confidence, color: qualityColor },
              { label: 'Relevance', value: evaluation.relevance_score, color: 'var(--accent-cyan, #22d3ee)' },
              { label: 'Completeness', value: evaluation.completeness_score, color: 'var(--accent-purple, #a78bfa)' },
            ].map(({ label, value, color }) => (
              <div key={label} className="eval-metric">
                <span className="eval-metric-label">{label}</span>
                <div className="eval-bar-wrap">
                  <div className="eval-bar-fill" style={{ width: `${Math.round((value || 0) * 100)}%`, background: color }} />
                </div>
                <span className="eval-metric-value">{Math.round((value || 0) * 100)}%</span>
              </div>
            ))}
          </div>
          <div className="eval-tags">
            <span className="eval-tag"><FileText size={11} /> {evaluation.evidence_count} evidence item{evaluation.evidence_count !== 1 ? 's' : ''}</span>
            <span className="eval-tag" title="Evidence density"><span style={{ letterSpacing: 2, fontSize: 10 }}>{densityDots}</span> {evaluation.evidence_density} density</span>
            <span className={`eval-tag ${evaluation.is_grounded ? 'grounded' : 'ungrounded'}`}>
              <Shield size={11} /> {evaluation.is_grounded ? 'Grounded' : 'Unverified'}
            </span>
            <span className="eval-tag"><Zap size={11} /> {evaluation.agents_used_count} agent{evaluation.agents_used_count !== 1 ? 's' : ''}</span>
            <span className="eval-tag intent">Intent: <code>{evaluation.intent_detected}</code></span>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Dataset Citations Panel ───────────────────────────────────────────────────
function CitationsPanel({ citations }) {
  const [open, setOpen] = useState(false)
  if (!citations || citations.length === 0) return null

  return (
    <div className="citations-panel">
      <button
        type="button"
        className="citations-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <Database size={13} />
        <span>Data Sources ({citations.length})</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>

      {open && (
        <div className="citations-list">
          {citations.map((c, i) => (
            <div key={i} className="citation-card">
              <div className="citation-header">
                <span className="citation-icon">{c.icon}</span>
                <div className="citation-title-block">
                  <span className="citation-name">{c.name}</span>
                  <span className="citation-granularity">{c.granularity}</span>
                </div>
                {c.url && (
                  <a href={c.url} target="_blank" rel="noopener noreferrer" className="citation-link" title="View source dataset">
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
              <p className="citation-description">{c.description}</p>
              <div className="citation-meta">
                <span className="citation-source-label">Source:</span>
                <span>{c.source}</span>
              </div>
              {c.fields && (
                <div className="citation-fields">
                  {c.fields.slice(0, 4).map(f => (
                    <code key={f} className="citation-field-chip">{f}</code>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Main Assistant Component ──────────────────────────────────────────────────
export default function Assistant() {
  const { lang, t } = useLanguage()

  // Load persisted history from localStorage
  const [messages, setMessages] = useState(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY)
      if (raw) return JSON.parse(raw).slice(-MAX_HISTORY)
    } catch { /* ignore */ }
    return []
  })

  const [value, setValue] = useState('')
  const [busy, setBusy] = useState(false)
  const [activeAudioIndex, setActiveAudioIndex] = useState(null)
  const [showVoiceHelp, setShowVoiceHelp] = useState(false)
  const [lastVoiceInput, setLastVoiceInput] = useState(false)
  const chatScrollRef = useRef(null)

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-MAX_HISTORY)))
    } catch { /* storage full */ }
  }, [messages])

  // Send query function
  const send = useCallback(async (textToSend, isFromVoice = false) => {
    const queryText = (textToSend != null ? textToSend : value || '').trim()
    if (!queryText || busy) return

    const pendingClarification = messages.at(-1)?.intent === 'period_clarification'
    const dateOnly = /^20\d{2}-\d{2}-\d{2}$/.test(queryText)
    const originalQuestion = pendingClarification
      ? [...messages].reverse().find(message => message.role === 'user')?.text
      : null
    const requestText = pendingClarification && dateOnly && originalQuestion
      ? `${originalQuestion} on ${queryText}`
      : queryText

    setMessages(prev => [...prev, { role: 'user', text: queryText, fromVoice: isFromVoice, ts: Date.now() }])
    setValue('')
    setBusy(true)
    setLastVoiceInput(isFromVoice)

    try {
      const res = await ask(requestText, lang)
      setMessages(prev => [...prev, { role: 'assistant', ...res, ts: Date.now() }])
      if (isFromVoice && res.answer) speak(res.warning || res.answer)
    } catch (e) {
      const errMsg = e.response?.data?.error?.message || e.response?.data?.detail || 'The API is unavailable. Please check that FastAPI is running.'
      setMessages(prev => [...prev, { role: 'assistant', answer: errMsg, evidence: [], agents_used: [], confidence: 0, is_relevant: true, citations: [], evaluation: null, ts: Date.now() }])
    } finally {
      setBusy(false)
    }
  }, [value, busy, lang, messages])

  // Voice Hook
  const {
    supported: voiceSupported, ttsSupported, isListening, transcript,
    isSpeaking, voiceError, startListening, stopListening, speak, stopSpeaking
  } = useVoice(lang, (parsed) => {
    if (parsed.type === 'action') {
      if (parsed.action === 'clear') { setMessages([]); speak('Chat cleared.') }
      else if (parsed.action === 'stop_audio') stopSpeaking()
      else if (parsed.action === 'read_latest') {
        const lastMsg = [...messages].reverse().find(m => m.role === 'assistant')
        if (lastMsg?.answer) speak(lastMsg.warning || lastMsg.answer)
      }
    }
  })

  // Auto-scroll
  useEffect(() => {
    chatScrollRef.current?.scrollTo({ top: chatScrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy, transcript])

  function handleVoiceClick() {
    if (isListening) stopListening()
    else startListening((text) => { if (text?.trim().length >= 3) { setValue(text); send(text, true) } }, { autoSubmit: true })
  }

  function handleSpeak(index, answerText) {
    if (isSpeaking && activeAudioIndex === index) { stopSpeaking(); setActiveAudioIndex(null) }
    else { setActiveAudioIndex(index); speak(answerText) }
  }

  function clearHistory() {
    setMessages([])
    stopSpeaking()
    try { localStorage.removeItem(HISTORY_KEY) } catch { /* ignore */ }
  }

  function relativeTime(ts) {
    if (!ts) return ''
    const d = Date.now() - ts
    if (d < 60000) return 'Just now'
    if (d < 3600000) return `${Math.floor(d / 60000)}m ago`
    if (d < 86400000) return `${Math.floor(d / 3600000)}h ago`
    return new Date(ts).toLocaleDateString()
  }

  const suggestions = t('suggestions') || [
    'What was the peak electricity demand?',
    'What is the expected demand for the next 6 hours?',
    'Compare weekday and weekend consumption.',
    'Identify unusual consumption patterns.'
  ]

  const assistantMsgCount = messages.filter(m => m.role === 'assistant').length

  return (
    <>
      <header className="page-header">
        <div>
          <div className="eyebrow">{t('overviewEyebrow', 'WORKSPACE · AI ASSISTANT')}</div>
          <h1>{t('assistantTitle', 'Ask Your Energy Data')}</h1>
          <p>{t('assistantSubtitle', 'Every answer is grounded in analytics with dataset citations and quality evaluation.')}</p>
        </div>
        <div className="header-actions">
          {messages.length > 0 && (
            <>
              <span className="history-count-badge">
                <RotateCcw size={11} /> {assistantMsgCount} response{assistantMsgCount !== 1 ? 's' : ''} in history
              </span>
              <button type="button" className="icon-button" onClick={clearHistory} title="Clear chat history" aria-label="Clear chat history">
                <Trash2 size={16} />
              </button>
            </>
          )}
          <button type="button" className={`icon-button ${showVoiceHelp ? 'active' : ''}`} onClick={() => setShowVoiceHelp(!showVoiceHelp)} title="Voice Commands Guide" aria-label="Voice Commands Guide">
            <HelpCircle size={16} />
          </button>
          <div className="ai-ready">
            <span className="status-dot ok" /> {t('analyticsReady', 'Guardrails active')}
          </div>
        </div>
      </header>

      {showVoiceHelp && (
        <div className="voice-help-card">
          <div className="voice-help-header">
            <div className="voice-help-title"><Mic size={16} className="text-cyan" /><b>Voice Command &amp; Guardrail Guide</b></div>
            <button type="button" className="close-help-btn" onClick={() => setShowVoiceHelp(false)}>×</button>
          </div>
          <div className="voice-help-grid">
            <div className="voice-help-item"><span className="voice-badge">Ask Query</span><p>Speak naturally: <i>"What was the electricity demand during peak hours?"</i></p></div>
            <div className="voice-help-item"><span className="voice-badge">Action</span><p>Say <b>"Clear chat"</b> to reset history or <b>"Read answer"</b> to listen.</p></div>
            <div className="voice-help-item"><span className="voice-badge">Navigate</span><p>Say <b>"Go to dashboard"</b>, <b>"Go to analytics"</b>, or <b>"Go to anomalies"</b>.</p></div>
            <div className="voice-help-item"><span className="voice-badge">Guardrails</span><p>Off-topic queries trigger an alert card and guide you back to energy topics.</p></div>
          </div>
        </div>
      )}

      <div className="assistant-shell">
        <div className="chat-scroll" ref={chatScrollRef}>
          {!messages.length ? (
            <div className="welcome">
              <div className="welcome-icon"><Sparkles size={22} /></div>
              <h2>{t('whatToUnderstand', 'What would you like to understand?')}</h2>
              <p>{t('welcomeSub', 'Ask about demand peaks, unusual readings, load forecasts, or historical patterns.')}</p>
              <div className="suggestion-grid">
                {suggestions.map((s, idx) => (
                  <button key={idx} type="button" onClick={() => send(s)}><span>{s}</span><ArrowUp size={14} /></button>
                ))}
              </div>
              {voiceSupported && (
                <div className="voice-tip-box" onClick={handleVoiceClick} style={{ cursor: 'pointer' }}>
                  <Mic size={15} className="pulse-cyan" />
                  <span><b>Voice Commands active:</b> Click the mic or tap here to speak your question directly.</span>
                </div>
              )}
            </div>
          ) : (
            messages.map((m, i) => (
              <div key={i} className={`message ${m.role}`}>
                <div className="message-avatar">
                  {m.role === 'user' ? <User size={16} />
                    : (m.is_relevant === false || m.intent === 'out_of_scope') ? <AlertTriangle size={17} className="text-amber" />
                    : <Bot size={17} />}
                </div>
                <div className="message-body">
                  {m.role === 'user' ? (
                    <div className="user-message-content">
                      <p>{m.text}</p>
                      <div className="user-message-meta">
                        {m.fromVoice && <span className="voice-indicator-chip" title="Asked via voice command"><Mic size={11} /> Voice</span>}
                        {m.ts && <span className="message-timestamp">{relativeTime(m.ts)}</span>}
                      </div>
                    </div>
                  ) : (
                    <>
                      {m.is_relevant === false || m.intent === 'out_of_scope' ? (
                        <div className="guardrail-warning-card">
                          <div className="guardrail-badge"><AlertTriangle size={15} /><span>GUARDRAIL WARNING · OUT OF SCOPE</span></div>
                          <div className="guardrail-content"><p className="guardrail-text">{m.answer || m.warning}</p></div>
                          {m.suggested_queries?.length > 0 && (
                            <div className="guardrail-suggestions">
                              <span className="suggestion-label"><Sparkles size={13} /> Suggested Energy Queries:</span>
                              <div className="suggestion-chips">
                                {m.suggested_queries.map((q, qIdx) => (
                                  <button key={qIdx} type="button" className="chip-btn" onClick={() => send(q)}><span>{q}</span><ArrowUp size={12} /></button>
                                ))}
                              </div>
                            </div>
                          )}
                          {ttsSupported && (
                            <div className="guardrail-actions">
                              <button type="button" className="audio-btn" onClick={() => handleSpeak(i, m.answer || m.warning)}>
                                {isSpeaking && activeAudioIndex === i ? <VolumeX size={14} /> : <Volume2 size={14} />}
                                <span>{isSpeaking && activeAudioIndex === i ? 'Stop' : 'Listen to warning'}</span>
                              </button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <>
                          <div className="answer-label">
                            <Sparkles size={14} /> {m.intent === 'greeting' ? 'SMART GRID ASSISTANT' : t('energyInsightTitle', 'ENERGY INSIGHT')}
                            {m.intent !== 'greeting' && (
                              <span className="confidence">{Math.round((m.confidence || 0) * 100)}% {t('confidence', 'confidence')}</span>
                            )}
                            {ttsSupported && m.answer && (
                              <button type="button" className={`audio-btn ${isSpeaking && activeAudioIndex === i ? 'playing' : ''}`}
                                onClick={() => handleSpeak(i, m.answer)}
                                title={isSpeaking && activeAudioIndex === i ? t('stopAudio', 'Stop audio') : t('readAloud', 'Read aloud')}
                                aria-label={t('readAloud', 'Read aloud')}>
                                {isSpeaking && activeAudioIndex === i ? <VolumeX size={14} /> : <Volume2 size={14} />}
                                <span>{isSpeaking && activeAudioIndex === i ? t('stopAudio', 'Stop') : t('readAloud', 'Listen')}</span>
                              </button>
                            )}
                            {m.ts && <span className="message-timestamp">{relativeTime(m.ts)}</span>}
                          </div>
                          <p className="answer-text">{m.answer}</p>

                          {m.intent !== 'greeting' && (
                            <AssistantPictorial chartData={m.chart_data} chartType={m.chart_type} chartTitle={m.chart_title} intent={m.intent} evidence={m.evidence} />
                          )}

                          {m.suggested_queries?.length > 0 && (
                            <div className="suggestion-chips" style={{ marginTop: '0.85rem' }}>
                              {m.suggested_queries.map((q, qIdx) => (
                                <button key={qIdx} type="button" className="chip-btn" onClick={() => send(q)}><span>{q}</span><ArrowUp size={12} /></button>
                              ))}
                            </div>
                          )}

                          {m.evidence?.length > 0 && (
                            <details className="evidence">
                              <summary><FileText size={14} /> {t('supportingEvidence', 'Supporting evidence')} ({m.evidence.length}) <ChevronDown size={14} /></summary>
                              <div className="evidence-list">
                                {m.evidence.slice(0, 10).map((e, j) => (
                                  <div key={j}>
                                    <span>{e.label || e.timestamp || e.task || 'Reading'}</span>
                                    <b>{e.value ?? e.demand ?? e.actual_value ?? e.predicted_demand ?? '—'}{e.unit ? ` ${e.unit}` : e.actual_value != null ? ' kW' : ''}</b>
                                  </div>
                                ))}
                              </div>
                            </details>
                          )}

                          {/* ── Dataset Citations ── */}
                          <CitationsPanel citations={m.citations} />

                          {/* ── Per-message Evaluation ── */}
                          <EvalWidget evaluation={m.evaluation} />

                          <div className="agent-chips">
                            {m.agents_used?.map(a => <span key={a}><Check size={12} />{a.replaceAll('_', ' ')}</span>)}
                          </div>

                          {m.trace_id && (
                            <Link className="trace-link" to="/trace" state={{ traceId: m.trace_id }}>
                              <Radio size={13} /> {t('viewAgentTrace', 'View agent trace')}
                            </Link>
                          )}
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}

          {busy && (
            <div className="thinking">
              <LoaderCircle size={16} /> {t('analyzingQuestion', 'Analyzing your question against smart grid models…')}
            </div>
          )}

          {isListening && (
            <div className="voice-listening-banner">
              <div className="voice-wave-container">
                <span className="wave-bar bar1" /><span className="wave-bar bar2" /><span className="wave-bar bar3" />
                <span className="wave-bar bar4" /><span className="wave-bar bar5" />
              </div>
              <div className="voice-listening-info">
                <b>🎙️ {t('listening', 'Voice Command Active… speak your question or command')}</b>
                {transcript ? <p className="live-transcript">"{transcript}"</p> : <p className="voice-sub-hint">"What was the peak demand?" or "Clear chat"</p>}
              </div>
              <button type="button" className="btn-stop-mic" onClick={stopListening}>{t('stopListening', 'Done')}</button>
            </div>
          )}

          {voiceError && <div className="notice error voice-notice"><span>{voiceError}</span></div>}
        </div>

        <form className="composer" onSubmit={e => { e.preventDefault(); send() }}>
          <textarea
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
            placeholder={t('composerPlaceholder', 'Ask a question or click the microphone to speak…')}
            rows="1"
          />
          <div className="composer-actions">
            {voiceSupported && (
              <button type="button" className={`voice-mic-btn ${isListening ? 'listening' : ''}`} onClick={handleVoiceClick}
                title={isListening ? t('stopListening', 'Stop voice command') : t('voiceInput', 'Voice Command')}
                aria-label={t('voiceInput', 'Voice Command')}>
                {isListening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>
            )}
            <button type="submit" className="send-btn" disabled={!value.trim() || busy} aria-label="Send message">
              <ArrowUp size={18} />
            </button>
          </div>
          <small>{t('sendHint', 'Enter to send · History auto-saved · Citations and evaluation included per response')}</small>
        </form>

        <div className="chat-foot">
          <span><Zap size={13} /> {t('evidenceBacked', 'Evidence-backed responses with domain guardrails')}</span>
          <span><Database size={13} /> Dataset citations &amp; evaluation per response</span>
        </div>
      </div>
    </>
  )
}
