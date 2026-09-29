import { useState, useRef, useEffect } from 'react'
import { Globe, ChevronDown, Check } from 'lucide-react'
import { useLanguage } from '../utils/i18n'

export default function LanguageSelector() {
  const { lang, setLang, languages } = useLanguage()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const current = languages.find(l => l.code === lang) || languages[0]

  return (
    <div className="lang-selector-wrap" ref={ref}>
      <button 
        type="button"
        className={`lang-button ${open ? 'active' : ''}`} 
        onClick={() => setOpen(!open)}
        title="Select Language"
        aria-label="Select Language"
      >
        <span className="lang-flag">{current.flag}</span>
        <span className="lang-code">{current.code.toUpperCase()}</span>
        <ChevronDown size={13} className={`lang-chevron ${open ? 'rotated' : ''}`} />
      </button>

      {open && (
        <div className="lang-dropdown">
          <div className="lang-dropdown-header">
            <Globe size={13} />
            <span>Select language</span>
          </div>
          <div className="lang-list">
            {languages.map(item => (
              <button
                key={item.code}
                type="button"
                className={`lang-option ${item.code === lang ? 'selected' : ''}`}
                onClick={() => {
                  setLang(item.code)
                  setOpen(false)
                }}
              >
                <span className="lang-flag">{item.flag}</span>
                <span className="lang-name">{item.name}</span>
                {item.code === lang && <Check size={14} className="lang-check" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
