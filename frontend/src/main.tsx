import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'
import { CalendarDays } from 'lucide-react'

class AppBoundary extends React.Component<React.PropsWithChildren, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  returnToLogin = () => { localStorage.removeItem('grade.session'); window.location.reload() }
  render() {
    if (this.state.failed) return <div className="app-error"><section><i><CalendarDays size={21} /></i><h1>Não foi possível abrir a grade</h1><p>Seu acesso e os horários continuam salvos. Volte ao acesso da escola e tente novamente.</p><button onClick={this.returnToLogin}>Voltar ao acesso</button></section></div>
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><AppBoundary><App /></AppBoundary></React.StrictMode>)
