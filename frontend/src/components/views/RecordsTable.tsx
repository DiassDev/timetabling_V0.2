import { Pencil, Plus, Trash2 } from 'lucide-react'
import type { Account, Data, Role, Row, Screen } from '../shared/types'
import {
  emptyHeading,
  emptyText,
  resolveAcademicName,
  resolveProfessorName,
} from '../shared/utils'
import { EmptyState } from '../ui/EmptyState'

type RecordsTableProps = {
  screen: Screen
  rows: Row[]
  data: Data
  accounts: Account[]
  role: Role
  onEdit: (row: Row) => void
  onDelete: (row: Row) => void
  onAvailabilityCreate: () => void
}

export function RecordsTable({
  screen,
  rows,
  data,
  accounts,
  role,
  onEdit,
  onDelete,
  onAvailabilityCreate,
}: RecordsTableProps) {
  const section =
    screen === 'Alocações'
      ? 'allocations'
      : screen === 'Disponibilidade'
        ? 'availability'
        : screen === 'Estrutura acadêmica'
          ? 'academic'
          : 'slots'

  const headers =
    section === 'allocations'
      ? ['Horário', 'Matéria', 'Professor', 'Turma', 'Aulas / semana']
      : section === 'availability'
        ? ['Professor', 'Horário disponível']
        : section === 'academic'
          ? ['Tipo', 'Nome', 'Detalhes']
          : ['Dia', 'Turno', 'Início', 'Duração']

  const value = (r: Row, key: string) => {
    if (key === 'slotId') {
      if (!r.slotId) return 'Automático (gerador)'
      const slot = data.slots.find(s => s.id === r.slotId)
      return slot
        ? `${slot.dia} · ${slot.inicio} (${slot.turno})`
        : 'Horário removido'
    }
    if (section === 'allocations' && key === 'materia') {
      return resolveAcademicName(data, r.materia)
    }
    if (section === 'allocations' && key === 'turma') {
      return resolveAcademicName(data, r.turma)
    }
    if (section === 'allocations' && key === 'professor') {
      return resolveProfessorName(accounts, r.professor)
    }
    if (section === 'academic' && key === 'detalhes' && r.turno) {
      return r.detalhes ? `${r.detalhes} (${r.turno})` : r.turno
    }
    return r[key] || '—'
  }

  const canEdit = section !== 'slots' || role !== 'PROFESSOR'

  return (
    <section className="table-panel">
      <div className="table-title">
        <div>
          <h2>
            {screen === 'Alocações'
              ? 'Aulas cadastradas'
              : screen === 'Disponibilidade'
                ? 'Horários disponíveis'
                : screen === 'Estrutura acadêmica'
                  ? 'Cursos, turmas e matérias'
                  : 'Horários-base'}
          </h2>
          <p>
            {screen === 'Alocações'
              ? 'Defina matéria, professor, turma e carga semanal para o motor distribuir os horários.'
              : screen === 'Disponibilidade'
                ? 'Os professores informam quando podem dar aulas.'
                : screen === 'Slots de horário'
                  ? 'Estes horários são definidos pela administração e coordenação.'
                  : 'Informações usadas para montar e consultar a grade.'}
          </p>
        </div>
        {screen === 'Disponibilidade' && role === 'PROFESSOR' && (
          <button className="btn primary" onClick={onAvailabilityCreate}>
            <Plus size={14} />
            Adicionar horário
          </button>
        )}
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {headers.map(h => (
                <th key={h}>{h}</th>
              ))}
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map(row => (
              <tr key={row.id}>
                {headers.map((h, i) => {
                  const keys =
                    section === 'allocations'
                      ? ['slotId', 'materia', 'professor', 'turma', 'aulas']
                      : section === 'availability'
                        ? ['email', 'slotId']
                        : section === 'academic'
                          ? ['tipo', 'nome', 'detalhes']
                          : ['dia', 'turno', 'inicio', 'duracao']
                  let v = value(row, keys[i])
                  if (section === 'availability' && keys[i] === 'email') {
                    v = resolveProfessorName(accounts, v)
                  }
                  return <td key={h}>{v}</td>
                })}
                <td className="row-controls">
                  {canEdit && role !== 'PROFESSOR' && (
                    <button
                      className="icon"
                      title="Editar"
                      onClick={() => onEdit(row)}
                    >
                      <Pencil size={14} />
                    </button>
                  )}
                  {section === 'availability' && role === 'PROFESSOR' && (
                    <button
                      className="icon"
                      title="Editar"
                      onClick={() => onEdit(row)}
                    >
                      <Pencil size={14} />
                    </button>
                  )}
                  {canEdit && role !== 'PROFESSOR' && (
                    <button
                      className="icon danger"
                      title="Remover"
                      onClick={() => onDelete(row)}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                  {section === 'availability' && role === 'PROFESSOR' && (
                    <button
                      className="icon danger"
                      title="Remover"
                      onClick={() => onDelete(row)}
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length === 0 && (
        <EmptyState title={emptyHeading(screen)} text={emptyText(screen)} />
      )}

      <div className="table-foot">
        {rows.length} {rows.length === 1 ? 'registro' : 'registros'}
        <span>
          {section === 'slots'
            ? 'Somente a administração e a coordenação podem alterar estes horários.'
            : ''}
        </span>
      </div>
    </section>
  )
}
