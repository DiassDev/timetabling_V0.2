import { FormEvent, useState } from 'react'
import { Check, X } from 'lucide-react'
import { labels, weekDays } from '../shared/constants'
import type { Account, Data, Field, Role, Row, Screen } from '../shared/types'
import { id, toMinutes } from '../shared/utils'
import { FieldInput } from '../ui/FieldInput'

type EditorModalProps = {
  screen: Screen
  row: Row
  data: Data
  accounts: Account[]
  role: Role
  onClose: () => void
  onSave: (row: Row) => void
}

export function EditorModal({
  screen,
  row,
  data,
  accounts,
  role,
  onClose,
  onSave,
}: EditorModalProps) {
  const [form, setForm] = useState<Row>(row)
  const [error, setError] = useState('')

  const change = (key: string, value: string) =>
    setForm(old => ({ ...old, [key]: value }))

  const accountMode = screen === 'Usuários'
  const slotMode = screen === 'Slots de horário'
  const allocation = screen === 'Alocações'
  const availability = screen === 'Disponibilidade'
  const academic = screen === 'Estrutura acadêmica'
  const teacher = role === 'PROFESSOR'

  const slotOptions: [string, string][] = data.slots.map(s => [
    s.id,
    `${s.dia} · ${s.inicio} · ${s.turno}`,
  ])

  const fields: Field[] = accountMode
    ? [
        { key: 'name', label: 'Nome', type: 'text' },
        { key: 'email', label: 'E-mail', type: 'email' },
        { key: 'password', label: 'Senha provisória', type: 'password' },
      ]
    : slotMode
      ? [
          {
            key: 'dia',
            label: 'Dia da semana',
            type: 'select',
            options: weekDays.map(d => [d, d]),
          },
          {
            key: 'turno',
            label: 'Turno',
            type: 'select',
            options: [
              ['Manhã', 'Manhã'],
              ['Tarde', 'Tarde'],
              ['Noite', 'Noite'],
            ],
          },
          { key: 'inicio', label: 'Horário de início', type: 'time' },
          { key: 'duracao', label: 'Duração (minutos)', type: 'number' },
        ]
      : allocation
        ? [
            {
              key: 'materia',
              label: 'Matéria',
              type: 'select',
              options: data.academic
                .filter(a => a.tipo === 'Disciplina')
                .map(a => [a.id, a.nome]),
            },
            {
              key: 'professor',
              label: 'Professor',
              type: 'select',
              options: accounts
                .filter(a => a.role === 'PROFESSOR')
                .map(a => [a.email, a.name]),
            },
            {
              key: 'turma',
              label: 'Turma',
              type: 'select',
              options: data.academic
                .filter(a => a.tipo === 'Turma')
                .map(a => [a.id, a.nome]),
            },
            { key: 'aulas', label: 'Aulas por semana', type: 'number' },
            {
              key: 'slotId',
              label: 'Horário preferencial (opcional)',
              type: 'select',
              options: slotOptions,
              required: false,
            },
          ]
        : availability
          ? teacher
            ? [
                {
                  key: 'slotId',
                  label: 'Horário disponível',
                  type: 'select',
                  options: slotOptions,
                },
              ]
            : [
                {
                  key: 'email',
                  label: 'Professor',
                  type: 'select',
                  options: accounts
                    .filter(a => a.role === 'PROFESSOR')
                    .map(a => [a.email, a.name]),
                },
                {
                  key: 'slotId',
                  label: 'Horário disponível',
                  type: 'select',
                  options: slotOptions,
                },
              ]
          : academic
            ? [
                {
                  key: 'tipo',
                  label: 'Tipo de cadastro',
                  type: 'select',
                  options: [
                    ['Curso', 'Curso'],
                    ['Turma', 'Turma'],
                    ['Disciplina', 'Matéria'],
                  ],
                },
                { key: 'nome', label: 'Nome', type: 'text' },
                ...(form.tipo === 'Turma'
                  ? [
                      {
                        key: 'turno',
                        label: 'Turno da turma',
                        type: 'select',
                        options: [
                          ['Manhã', 'Manhã'],
                          ['Tarde', 'Tarde'],
                          ['Noite', 'Noite'],
                        ] as [string, string][],
                      },
                    ]
                  : []),
                { key: 'detalhes', label: 'Detalhes', type: 'text' },
              ]
            : []

  const submit = (e: FormEvent) => {
    e.preventDefault()
    setError('')

    const missing = fields.some(
      f => f.required !== false && !String(form[f.key] || '').trim()
    )
    if (missing) {
      setError('Preencha todos os campos.')
      return
    }

    if (slotMode) {
      const from = toMinutes(form.inicio)
      const to = from + Number(form.duracao)
      if (!Number(form.duracao) || to > 1440) {
        setError('Confira o horário e a duração.')
        return
      }
      const clash = data.slots.some(
        s =>
          s.id !== form.id &&
          s.dia === form.dia &&
          s.turno === form.turno &&
          from < toMinutes(s.inicio) + Number(s.duracao) &&
          toMinutes(s.inicio) < to
      )
      if (clash) {
        setError(
          'Esse horário se sobrepõe a outro. Ajuste o início ou a duração.'
        )
        return
      }
    }

    if (
      accountMode &&
      accounts.some(
        a =>
          a.email.toLowerCase() === form.email.toLowerCase() &&
          a.id !== form.id
      )
    ) {
      setError('Já existe um acesso com esse e-mail.')
      return
    }

    const rowOut: Row = { ...form, id: form.id || id() }
    if (teacher && availability) {
      rowOut.email =
        accounts.find(a => a.role === 'PROFESSOR' && a.email === row.email)
          ?.email || row.email
    }
    onSave(rowOut)
  }

  const heading = accountMode
    ? 'Cadastro de ' + labels[row.role as Role].toLowerCase()
    : slotMode
      ? 'Novo horário-base'
      : allocation
        ? 'Nova aula'
        : availability
          ? 'Horário disponível'
          : 'Novo cadastro'

  return (
    <div
      className="backdrop"
      onMouseDown={e => e.target === e.currentTarget && onClose()}
    >
      <section className="modal">
        <div className="modal-top">
          <div>
            <p className="login-overline">
              {screen === 'Alocações'
                ? 'AULA'
                : screen === 'Disponibilidade'
                  ? 'DISPONIBILIDADE'
                  : 'CADASTRO'}
            </p>
            <h2>{heading}</h2>
          </div>
          <button className="icon" onClick={onClose} aria-label="Fechar">
            <X size={18} />
          </button>
        </div>

        <form className="editor-form" onSubmit={submit}>
          {fields.map(field => (
            <FieldInput
              key={field.key}
              field={field}
              value={form[field.key] || ''}
              onChange={v => change(field.key, v)}
            />
          ))}
          {error && <p className="form-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="btn secondary" onClick={onClose}>
              Cancelar
            </button>
            <button className="btn primary">
              <Check size={15} />
              Salvar
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
