import { AlertCircle, LoaderCircle } from 'lucide-react'

export function LoadingState({ label = 'Loading energy data…' }) {
  return (
    <div className="loading-state">
      <LoaderCircle size={18} className="spinner" />
      {label}
    </div>
  )
}

export function ErrorState({ message = 'Unable to load data. Check the FastAPI and MongoDB services.' }) {
  return <div className="notice error"><AlertCircle size={17} /><span>{message}</span></div>
}
