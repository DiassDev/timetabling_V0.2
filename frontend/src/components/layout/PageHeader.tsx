import { Download, Plus } from 'lucide-react'
import { labels } from '../shared/constants'
import type { Account, Screen } from '../shared/types'
import { screenDescription } from '../shared/utils'

type PageHeaderProps = {
  screen: Screen
  active: Account
  addAction: string
  onExportSchedule: () => void
  onCreateNew: () => void
}

export function PageHeader({
  screen,
  active,
  addAction,
  onExportSchedule,
  onCreateNew,
}: PageHeaderProps) {
  const title =
    screen === 'Visão geral' ? 'Olá, ' + active.name.split(' ')[0] : screen

  return (
    <div className="heading">
      <div>
        <div className="eyebrow">
          <i /> INSTITUTO FAROL <span>/</span>{' '}
          {labels[active.role].toUpperCase()}
        </div>
        <h1>
          {title}
          {screen === 'Horários' && <small> · Grade da escola</small>}
        </h1>
        <p>{screenDescription(screen, active.role)}</p>
      </div>

      <div className="actions">
        {screen === 'Horários' && (
          <button className="btn secondary" onClick={onExportSchedule}>
            <Download size={15} /> Baixar horários
          </button>
        )}
        {addAction && (
          <button className="btn primary" onClick={onCreateNew}>
            <Plus size={15} />
            {addAction}
          </button>
        )}
      </div>
    </div>
  )
}
