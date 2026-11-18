import {
  CalendarDays,
  ChevronDown,
  CircleHelp,
  LogOut,
  X,
} from 'lucide-react'
import { labels, screens } from '../shared/constants'
import type { Account, Screen } from '../shared/types'

type SidebarProps = {
  active: Account
  screen: Screen
  mobile: boolean
  allocationsCount: number
  onNavigate: (next: Screen) => void
  onCloseMobile: () => void
  onHelp: () => void
  onLogout: () => void
}

export function Sidebar({
  active,
  screen,
  mobile,
  allocationsCount,
  onNavigate,
  onCloseMobile,
  onHelp,
  onLogout,
}: SidebarProps) {
  const nav = screens[active.role]

  return (
    <>
      <aside className={'sidebar ' + (mobile ? 'open' : '')}>
        <div className="brand">
          <i>
            <CalendarDays size={17} />
          </i>
          grade<span>.</span>
          {mobile && (
            <button className="icon mobile-close" onClick={onCloseMobile}>
              <X size={18} />
            </button>
          )}
        </div>

        <div className="workspace">
          <b>IF</b>
          <span>
            <strong>Instituto Farol</strong>
            <small>Unidade Centro</small>
          </span>
          <ChevronDown size={15} />
        </div>

        <label className="caption">MENU PRINCIPAL</label>
        <nav>
          {nav.map(([label, Icon]) => (
            <button
              key={label}
              className={'nav-item ' + (screen === label ? 'active' : '')}
              onClick={() => onNavigate(label)}
            >
              <Icon size={17} />
              {label}
              {label === 'Horários' && allocationsCount > 0 && (
                <em>{allocationsCount}</em>
              )}
            </button>
          ))}
        </nav>

        <div className="side-bottom">
          <div className="help-card">
            <CircleHelp size={18} />
            <strong>Precisa de ajuda?</strong>
            <p>Consulte a equipe da sua escola.</p>
            <a onClick={onHelp}>Como podemos ajudar?</a>
          </div>

          <div className="user">
            <b>
              {active.name
                .split(' ')
                .map(s => s[0])
                .slice(0, 2)
                .join('')
                .toUpperCase()}
            </b>
            <span>
              <strong>{active.name}</strong>
              <small>{labels[active.role]}</small>
            </span>
            <button className="icon" title="Sair" onClick={onLogout}>
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {mobile && (
        <button
          className="scrim"
          onClick={onCloseMobile}
          aria-label="Fechar menu"
        />
      )}
    </>
  )
}
