import {
  ArrowLeft,
  LogOut,
  Menu,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { labels } from '../shared/constants'
import type { Role, Screen } from '../shared/types'

type HeaderProps = {
  screen: Screen
  role: Role
  canGoBack: boolean
  search: string
  isGenerating: boolean
  onSearchChange: (value: string) => void
  onGoBack: () => void
  onOpenMobileMenu: () => void
  onGenerateSchedule: () => void
  onLogout: () => void
}

export function Header({
  screen,
  role,
  canGoBack,
  search,
  isGenerating,
  onSearchChange,
  onGoBack,
  onOpenMobileMenu,
  onGenerateSchedule,
  onLogout,
}: HeaderProps) {
  return (
    <header className="top">
      <div className="crumb">
        {canGoBack && (
          <button
            className="icon back-screen"
            onClick={onGoBack}
            title="Voltar à tela anterior"
            aria-label="Voltar à tela anterior"
          >
            <ArrowLeft size={17} />
          </button>
        )}
        <button
          className="icon mobile-menu"
          onClick={onOpenMobileMenu}
          aria-label="Abrir menu"
        >
          <Menu size={19} />
        </button>
        Instituto Farol <i>/</i> <b>{screen}</b>
      </div>

      <div className="top-right">
        <button
          className="btn primary"
          onClick={onGenerateSchedule}
          disabled={isGenerating}
          title="Executar motor matemático (AG + Simulated Annealing)"
        >
          <Sparkles size={14} />
          {isGenerating ? 'Gerando...' : 'Gerar grade de horários'}
        </button>
        <label className="search">
          <Search size={15} />
          <input
            aria-label="Buscar"
            placeholder="Buscar..."
            value={search}
            onChange={e => onSearchChange(e.target.value)}
          />
        </label>
        <span className="role-chip">
          <ShieldCheck size={14} />
          {labels[role]}
        </span>
        <button className="icon" onClick={onLogout} title="Sair">
          <LogOut size={16} />
        </button>
      </div>
    </header>
  )
}
