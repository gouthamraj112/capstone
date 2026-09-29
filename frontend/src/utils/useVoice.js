import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'

const LANG_LOCALES = {
  en: 'en-US',
  es: 'es-ES',
  fr: 'fr-FR',
  de: 'de-DE',
  zh: 'zh-CN',
  hi: 'hi-IN'
}

export function useVoice(lang = 'en', onCommandRecognized = null) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [voiceError, setVoiceError] = useState('')
  const [audioLevel, setAudioLevel] = useState(0)
  const recognitionRef = useRef(null)
  const navigate = useNavigate()

  const supported = typeof window !== 'undefined' && Boolean(
    window.SpeechRecognition || window.webkitSpeechRecognition
  )
  const ttsSupported = typeof window !== 'undefined' && Boolean(window.speechSynthesis)

  // Voice Navigation and Action parser
  const handleVoiceCommand = useCallback((text) => {
    const t = text.toLowerCase().trim()

    // 1. Navigation triggers across languages
    const navMap = [
      { path: '/', triggers: ['go to dashboard', 'ir al panel', 'aller au tableau de bord', 'zum dashboard', '打开仪表板', 'डैशबोर्ड पर जाएं', 'open dashboard'] },
      { path: '/analytics', triggers: ['go to analytics', 'ir a analítica', 'ir a analitica', 'aller à l\'analytique', 'zur analytik', '查看分析', 'विश्लेषण पर जाएं', 'open analytics'] },
      { path: '/anomalies', triggers: ['go to anomalies', 'ir a anomalías', 'ir a anomalias', 'aller aux anomalies', 'zu anomalien', '查看异常', 'असामान्यताओं पर जाएं', 'open anomalies'] },
      { path: '/forecast', triggers: ['go to forecast', 'ir a pronóstico', 'ir a pronostico', 'aller aux prévisions', 'zur prognose', '查看预测', 'पूर्वानुमान पर जाएं', 'open forecast'] },
      { path: '/assistant', triggers: ['go to assistant', 'ir al asistente', 'aller à l\'assistant', 'zum assistenten', '打开助手', 'सहायक पर जाएं', 'open assistant'] },
      { path: '/trace', triggers: ['go to trace', 'ir a traza', 'aller au trace', 'zum trace', '查看追踪', 'ट्रेस पर जाएं', 'open trace'] },
      { path: '/evaluation', triggers: ['go to evaluation', 'ir a evaluación', 'ir a evaluacion', 'aller à l\'évaluation', 'zur bewertung', '查看评估', 'मूल्यांकन पर जाएं', 'open evaluation'] },
    ]

    for (const item of navMap) {
      if (item.triggers.some(cmd => t.includes(cmd))) {
        navigate(item.path)
        return { type: 'navigation', target: item.path }
      }
    }

    // 2. Control Action triggers
    const clearTriggers = [
      'clear chat', 'clear history', 'reset chat', 'new chat',
      'limpiar chat', 'borrar chat', 'nuevo chat',
      'effacer le chat', 'nouveau chat',
      'chat löschen', 'neuer chat',
      '清空对话', '清空聊天', '新建对话',
      'चैट साफ़ करें', 'नया चैट'
    ]
    if (clearTriggers.some(cmd => t.includes(cmd))) {
      return { type: 'action', action: 'clear' }
    }

    const stopAudioTriggers = [
      'stop talking', 'stop audio', 'stop reading', 'silence', 'mute',
      'silencio', 'detener voz', 'parar audio',
      'arreter la voix', 'stumm', 'stoppe sprache',
      '停止朗读', '静音', '停止说话',
      'आवाज़ बंद करें', 'चुप रहो'
    ]
    if (stopAudioTriggers.some(cmd => t.includes(cmd))) {
      if (ttsSupported) {
        window.speechSynthesis.cancel()
        setIsSpeaking(false)
      }
      return { type: 'action', action: 'stop_audio' }
    }

    const readAloudTriggers = [
      'read answer', 'read aloud', 'repeat answer', 'speak answer',
      'leer respuesta', 'leer en voz alta',
      'lire la reponse', 'lire a haute voix',
      'antwort vorlesen', 'vorlesen',
      '朗读回答', '大声朗读',
      'उत्तर पढ़कर सुनाओ'
    ]
    if (readAloudTriggers.some(cmd => t.includes(cmd))) {
      return { type: 'action', action: 'read_latest' }
    }

    // 3. Natural voice query: strip conversational command prefixes if present
    let queryText = text
    const prefixes = [
      /^(?:please\s+)?(?:ask|query|tell\s+me|find|show\s+me)\s+/i,
      /^(?:por\s+favor\s+)?(?:pregunta|muestra|dime|busca)\s+/i,
      /^(?:s'il\s+vous\s+plaît\s+)?(?:demande|montre|dis-moi)\s+/i,
      /^(?:bitte\s+)?(?:frage|zeige|sag\s+mir)\s+/i,
      /^(?:请问|请帮我查询|查询|请告诉我)\s*/i,
      /^(?:कृपया\s+)?(?:पूछें|दिखाएं|बताएं)\s+/i,
    ]
    for (const pat of prefixes) {
      if (pat.test(queryText)) {
        queryText = queryText.replace(pat, '').trim()
        break
      }
    }

    return { type: 'query', text: queryText }
  }, [navigate, ttsSupported])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch (err) {
        // Ignore if already stopped
      }
    }
    setIsListening(false)
  }, [])

  const startListening = useCallback((onResultText, options = {}) => {
    setVoiceError('')
    if (!supported) {
      setVoiceError('Speech recognition is not supported in this browser.')
      return
    }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRec()
    recognitionRef.current = recognition

    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = LANG_LOCALES[lang] || 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      setTranscript('')
    }

    recognition.onresult = (event) => {
      let currentText = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        currentText += event.results[i][0].transcript
      }
      setTranscript(currentText)

      if (event.results[0].isFinal) {
        const finalText = currentText.trim()
        const parsed = handleVoiceCommand(finalText)

        if (parsed.type === 'query') {
          if (onResultText) {
            onResultText(parsed.text, options.autoSubmit)
          }
        }

        if (onCommandRecognized) {
          onCommandRecognized(parsed, finalText)
        }
      }
    }

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error)
      if (event.error !== 'no-speech') {
        setVoiceError(`Voice error: ${event.error}`)
      }
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    try {
      recognition.start()
    } catch (e) {
      console.error('Failed to start speech recognition:', e)
      setIsListening(false)
    }
  }, [supported, lang, handleVoiceCommand, onCommandRecognized])

  // Text to Speech
  const speak = useCallback((text) => {
    if (!ttsSupported) return
    window.speechSynthesis.cancel()

    // Clean markdown/symbols from text before reading
    const cleanText = text
      .replace(/[*#_`~[\]]/g, '')
      .replace(/\(https?:\/\/[^\)]+\)/g, '')
      .replace(/⚠️/g, 'Warning. ')
      .replace(/⚡/g, '')
      .replace(/\s+/g, ' ')
      .trim()

    const utterance = new SpeechSynthesisUtterance(cleanText)
    utterance.lang = LANG_LOCALES[lang] || 'en-US'
    utterance.rate = 1.0

    // Pick best voice for language if available
    const voices = window.speechSynthesis.getVoices()
    const targetPrefix = (LANG_LOCALES[lang] || 'en').split('-')[0]
    const matchedVoice = voices.find(v => v.lang.startsWith(targetPrefix))
    if (matchedVoice) {
      utterance.voice = matchedVoice
    }

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    window.speechSynthesis.speak(utterance)
  }, [ttsSupported, lang])

  const stopSpeaking = useCallback(() => {
    if (ttsSupported) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }, [ttsSupported])

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch (e) {}
      }
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  return {
    supported,
    ttsSupported,
    isListening,
    transcript,
    isSpeaking,
    voiceError,
    startListening,
    stopListening,
    speak,
    stopSpeaking
  }
}
