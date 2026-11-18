import { useMemo, useState } from 'react'
import { CalendarDays, Check, Download, Sparkles, Users } from 'lucide-react'
import { weekDays } from '../shared/constants'
import type {
  Account,
  Data,
  GenerationResult,
  Role,
  ScheduledLesson,
} from '../shared/types'
import { resolveAcademicName, resolveProfessorName } from '../shared/utils'
import { EmptyState } from '../ui/EmptyState'

type ScheduleProps = {
  data: Data
  accounts: Account[]
  role: Role
  email: string
  generationResult: GenerationResult | null
  onExport: () => void
}

export function Schedule({
  data,
  accounts,
  role,
  email,
  generationResult,
  onExport,
}: ScheduleProps) {
  const [turn, setTurn] = useState('Manhã')
  const [selectedTurma, setSelectedTurma] = useState('Todas')

  const generatedLessons: ScheduledLesson[] = useMemo(() => {
    if (
      generationResult?.status === 'CONCLUIDA' &&
      generationResult.grade.length > 0
    ) {
      return generationResult.grade
    }

    return data.allocations
      .filter(a => Boolean(a.slotId))
      .map(a => {
        const slot = data.slots.find(s => s.id === a.slotId)
        return {
          id: a.id,
          alocacaoId: a.id,
          slotId: a.slotId || '',
          dia: slot?.dia || 'Segunda-feira',
          turno: slot?.turno || 'Manhã',
          inicio: slot?.inicio || '07:10',
          duracao: slot?.duracao || '50',
          materia: resolveAcademicName(data, a.materia),
          materiaId: a.materia || '',
          professor: resolveProfessorName(accounts, a.professor),
          professorEmail: a.professor || '',
          turma: resolveAcademicName(data, a.turma),
          turmaId: a.turma || '',
          curso: '',
          aulas: a.aulas || '1',
        }
      })
  }, [generationResult, data, accounts])

  const filteredByRole = useMemo(() => {
    if (role !== 'PROFESSOR') return generatedLessons
    const cleanEmail = email.trim().toLowerCase()
    return generatedLessons.filter(
      item =>
        item.professorEmail.toLowerCase() === cleanEmail ||
        item.professor.toLowerCase() === cleanEmail
    )
  }, [generatedLessons, role, email])

  const turmasOptions = useMemo(() => {
    const fromAcademic = data.academic
      .filter(a => a.tipo === 'Turma')
      .map(a => a.nome)
    const fromLessons = filteredByRole.map(l => l.turma).filter(Boolean)
    return ['Todas', ...new Set([...fromAcademic, ...fromLessons])]
  }, [data.academic, filteredByRole])

  const visibleLessons = useMemo(() => {
    return filteredByRole.filter(
      l =>
        l.turno === turn &&
        (selectedTurma === 'Todas' || l.turma === selectedTurma)
    )
  }, [filteredByRole, turn, selectedTurma])

  const activeSlots = data.slots.filter(s => s.turno === turn)
  const defaultTimes =
    turn === 'Manhã'
      ? ['07:10', '08:00', '08:50', '09:55', '10:45']
      : turn === 'Tarde'
        ? ['13:10', '14:00', '14:50', '15:55', '16:45']
        : ['19:00', '19:50', '20:40', '21:30']

  const times = [
    ...new Set([
      ...activeSlots.map(s => s.inicio),
      ...visibleLessons.map(l => l.inicio),
    ]),
  ].sort()
  const visibleTimes = times.length ? times : defaultTimes

  const metricas = generationResult?.metricas
  const falhou = generationResult?.status === 'FALHA'
  const concluida = generationResult?.status === 'CONCLUIDA'

  return (
    <section className="schedule">
      <div className="toolbar">
        <div>
          <span className="select">
            <CalendarDays size={14} /> Grade semanal
          </span>
          {turmasOptions.length > 1 && (
            <div className="table-actions">
              <select
                aria-label="Filtrar por turma"
                value={selectedTurma}
                onChange={e => setSelectedTurma(e.target.value)}
              >
                {turmasOptions.map(t => (
                  <option key={t} value={t}>
                    {t === 'Todas' ? 'Todas as turmas' : t}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        <div>
          <div className="seg">
            {['Manhã', 'Tarde', 'Noite'].map(t => (
              <button
                className={turn === t ? 'on' : ''}
                onClick={() => setTurn(t)}
                key={t}
              >
                {t}
              </button>
            ))}
          </div>
          <button className="btn secondary" onClick={onExport}>
            <Download size={14} /> Baixar horários
          </button>
        </div>
      </div>

      {falhou && generationResult.diagnosticos.length > 0 && (
        <div
          className="form-error"
          style={{ margin: '12px 15px', borderRadius: 8 }}
        >
          <strong>Não foi possível gerar a grade: </strong>
          {generationResult.diagnosticos.map(d => d.mensagem).join(' · ')}
        </div>
      )}

      <div className="weekbar">
        <strong>Horários da semana ({turn})</strong>
        <span className="legend">
          <i />{' '}
          {concluida
            ? `Grade otimizada (${filteredByRole.length} aulas)`
            : 'Aulas cadastradas'}
        </span>
      </div>

      <div className="grid-scroll">
        <div className="grid">
          <div className="time-head">HORÁRIO</div>
          {weekDays.slice(0, 5).map(d => (
            <div className="day" key={d}>
              {d.replace('-feira', '').toUpperCase()}
            </div>
          ))}

          {visibleTimes.map(time => (
            <div className="row" key={time}>
              <div className="time">
                <b>{time}</b>
                <small>
                  {activeSlots.find(s => s.inicio === time)?.duracao ||
                    visibleLessons.find(l => l.inicio === time)?.duracao ||
                    50}{' '}
                  min
                </small>
              </div>
              {weekDays.slice(0, 5).map(d => {
                const slot = activeSlots.find(
                  s => s.dia === d && s.inicio === time
                )
                const lessons = visibleLessons.filter(
                  l =>
                    (slot && l.slotId === slot.id) ||
                    (l.dia === d && l.inicio === time)
                )
                return (
                  <div className="cell" key={d}>
                    {lessons.map((a, i) => (
                      <div
                        className={
                          'lesson ' + ['blue', 'peach', 'green', 'purple'][i % 4]
                        }
                        key={a.id}
                      >
                        <b>{a.materia}</b>
                        <span>
                          {a.turma} ·{' '}
                          {role === 'PROFESSOR' ? 'Minha aula' : a.professor}
                        </span>
                        <small>
                          <Users size={10} />
                          {a.aulas} aulas por semana
                        </small>
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {concluida && metricas && (
        <div className="schedule-foot">
          <span>
            <Sparkles
              size={11}
              style={{ verticalAlign: 'middle', marginRight: 4 }}
            />
            Motor híbrido (AG + SA): <b>{generationResult.grade.length} aulas</b>{' '}
            · Conflitos fortes: <b>{metricas.violacoes_fortes}</b> · Janelas
            (prof: <b>{metricas.janelas_professor}</b>, turma:{' '}
            <b>{metricas.janelas_turma}</b>) · Tempo:{' '}
            <b>{metricas.tempo_execucao_segundos}s</b>
          </span>
          <button type="button">
            <Check size={12} /> Grade válida
          </button>
        </div>
      )}

      {filteredByRole.length === 0 && (
        <EmptyState
          title="Sua grade semanal está pronta"
          text="Clique em “Gerar grade de horários” no topo ou no painel para distribuir as aulas automaticamente."
        />
      )}
    </section>
  )
}
