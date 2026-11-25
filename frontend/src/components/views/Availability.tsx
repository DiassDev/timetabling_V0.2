import { useMemo, useState } from 'react'
import { Check, Clock3 } from 'lucide-react'
import { weekDays } from '../shared/constants'
import type { Account, Data, Role, Row } from '../shared/types'
import { id } from '../shared/utils'
import { EmptyState } from '../ui/EmptyState'

type AvailabilityProps = {
  data: Data
  accounts: Account[]
  role: Role
  email: string
  onChange: (availability: Row[]) => void
}

const turns = ['Manhã', 'Tarde', 'Noite']

// Grade semanal de disponibilidade: o professor marca/desmarca os slots em que pode lecionar;
// coordenação apenas consulta, escolhendo o professor.
export function Availability({
  data,
  accounts,
  role,
  email,
  onChange,
}: AvailabilityProps) {
  const teacher = role === 'PROFESSOR'
  const professors = accounts.filter(a => a.role === 'PROFESSOR')
  const [selected, setSelected] = useState(
    teacher ? email : professors[0]?.email || ''
  )
  const [turn, setTurn] = useState(
    () => turns.find(t => data.slots.some(s => s.turno === t)) || 'Manhã'
  )

  const target = teacher ? email : selected
  const marked = useMemo(
    () =>
      new Set(
        data.availability.filter(a => a.email === target).map(a => a.slotId)
      ),
    [data.availability, target]
  )

  const activeSlots = data.slots.filter(s => s.turno === turn)
  const times = [...new Set(activeSlots.map(s => s.inicio))].sort()
  const days = weekDays.slice(0, 5)

  // Alterna um slot na disponibilidade do próprio professor.
  const toggle = (slotId: string) => {
    if (!teacher) return
    onChange(
      marked.has(slotId)
        ? data.availability.filter(
            a => !(a.email === email && a.slotId === slotId)
          )
        : [...data.availability, { id: id(), email, slotId }]
    )
  }

  // Marca ou limpa todos os slots do turno exibido.
  const setTurn_ = (available: boolean) => {
    if (!teacher) return
    const ids = new Set(activeSlots.map(s => s.id))
    const others = data.availability.filter(
      a => !(a.email === email && ids.has(a.slotId))
    )
    onChange(
      available
        ? [...others, ...activeSlots.map(s => ({ id: id(), email, slotId: s.id }))]
        : others
    )
  }

  if (!data.slots.length) {
    return (
      <section className="schedule">
        <EmptyState
          title="Nenhum horário-base cadastrado"
          text="A disponibilidade é informada sobre os horários-base. Peça à coordenação ou ao administrador para cadastrá-los."
        />
      </section>
    )
  }

  return (
    <section className="schedule">
      <div className="toolbar">
        <div>
          <span className="select">
            <Clock3 size={14} /> {marked.size} de {data.slots.length} horários
            disponíveis
          </span>
          {!teacher && (
            <div className="table-actions">
              <select
                aria-label="Professor"
                value={selected}
                onChange={e => setSelected(e.target.value)}
              >
                {professors.length === 0 && (
                  <option value="">Nenhum professor cadastrado</option>
                )}
                {professors.map(p => (
                  <option key={p.email} value={p.email}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        <div>
          <div className="seg">
            {turns.map(t => (
              <button
                className={turn === t ? 'on' : ''}
                onClick={() => setTurn(t)}
                key={t}
              >
                {t}
              </button>
            ))}
          </div>
          {teacher && activeSlots.length > 0 && (
            <>
              <button className="btn secondary" onClick={() => setTurn_(true)}>
                Marcar turno
              </button>
              <button className="btn secondary" onClick={() => setTurn_(false)}>
                Limpar turno
              </button>
            </>
          )}
        </div>
      </div>

      <div className="weekbar">
        <strong>
          {teacher
            ? 'Clique nos horários em que você pode lecionar'
            : 'Disponibilidade informada pelo professor'}
        </strong>
        <span className="legend">
          <i /> Disponível
        </span>
      </div>

      {activeSlots.length === 0 ? (
        <EmptyState
          title={`Sem horários no turno ${turn}`}
          text="Escolha outro turno para informar a disponibilidade."
        />
      ) : (
        <div className="grid-scroll">
          <div className="grid">
            <div className="time-head">HORÁRIO</div>
            {days.map(d => (
              <div className="day" key={d}>
                {d.replace('-feira', '').toUpperCase()}
              </div>
            ))}
            {times.map(time => (
              <div className="row" key={time}>
                <div className="time">
                  <b>{time}</b>
                  <small>
                    {activeSlots.find(s => s.inicio === time)?.duracao} min
                  </small>
                </div>
                {days.map(d => {
                  const slot = activeSlots.find(
                    s => s.dia === d && s.inicio === time
                  )
                  if (!slot) return <div className="cell" key={d} />
                  const on = marked.has(slot.id)
                  return (
                    <div className="cell" key={d}>
                      <button
                        type="button"
                        className={'avail-cell ' + (on ? 'on' : '')}
                        disabled={!teacher}
                        aria-pressed={on}
                        onClick={() => toggle(slot.id)}
                      >
                        {on ? (
                          <>
                            <Check size={14} /> Disponível
                          </>
                        ) : (
                          'Indisponível'
                        )}
                      </button>
                    </div>
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
