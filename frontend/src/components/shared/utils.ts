import { useEffect, useState } from 'react'
import type { Account, Data, Role, Row, Screen } from './types'

export const id = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

export function toMinutes(value: string) {
  const [h, m] = String(value || '00:00')
    .split(':')
    .map(Number)
  return h * 60 + m
}

export const sectionFor = (s: Screen): keyof Data | undefined =>
  s === 'Alocações'
    ? 'allocations'
    : s === 'Disponibilidade'
      ? 'availability'
      : s === 'Estrutura acadêmica'
        ? 'academic'
        : s === 'Slots de horário'
          ? 'slots'
          : undefined

export function resolveAcademicName(data: Data, idOrName: string): string {
  if (!idOrName) return '—'
  const found = data.academic.find(
    a => a.id === idOrName || a.nome?.toLowerCase() === idOrName.toLowerCase()
  )
  return found?.nome || idOrName
}

export function resolveProfessorName(
  accounts: Account[],
  emailOrId: string
): string {
  if (!emailOrId) return '—'
  const found = accounts.find(
    a =>
      a.email.toLowerCase() === emailOrId.toLowerCase() ||
      a.id === emailOrId ||
      a.name.toLowerCase() === emailOrId.toLowerCase()
  )
  return found?.name || emailOrId
}

export function emptyHeading(s: Screen) {
  return s === 'Alocações'
    ? 'Nenhuma aula cadastrada ainda'
    : s === 'Disponibilidade'
      ? 'Nenhum horário informado ainda'
      : s === 'Estrutura acadêmica'
        ? 'Sua escola ainda não tem cadastros'
        : s === 'Slots de horário'
          ? 'Os horários-base ainda não foram definidos'
          : 'Nenhum registro encontrado'
}

export function emptyText(s: Screen) {
  return s === 'Alocações'
    ? 'Adicione uma aula escolhendo matéria, professor, turma e carga semanal.'
    : s === 'Disponibilidade'
      ? 'Adicione os horários em que pode dar aulas.'
      : s === 'Estrutura acadêmica'
        ? 'Cadastre cursos, turmas e matérias para usar nas aulas.'
        : s === 'Slots de horário'
          ? 'Cadastre os horários em que as aulas acontecem.'
          : 'Adicione um registro para começar.'
}

export function screenDescription(s: Screen, role: Role) {
  if (s === 'Visão geral') {
    return 'Acompanhe os próximos passos da organização escolar.'
  }
  if (s === 'Horários') {
    return 'Consulte as aulas organizadas por dia e horário.'
  }
  if (s === 'Alocações') {
    return 'Defina o horário, matéria, professor e turma de cada aula.'
  }
  if (s === 'Disponibilidade') {
    return role === 'PROFESSOR'
      ? 'Informe os dias e horários em que pode dar aulas.'
      : 'Consulte os horários disponíveis dos professores.'
  }
  if (s === 'Slots de horário') {
    return 'Defina os horários-base das aulas por dia e turno.'
  }
  if (s === 'Usuários') {
    return 'Gerencie quem pode acessar os horários da escola.'
  }
  return 'Mantenha cursos, turmas e matérias organizados.'
}

export function useStoredState<T>(
  key: string,
  fallback: T
): [T, (value: T | ((old: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) return fallback

      const parsed: unknown = JSON.parse(raw)

      if (key === 'grade.accounts') {
        if (!Array.isArray(parsed)) return fallback
        return parsed.filter((a): a is Account =>
          Boolean(
            a &&
              typeof a.id === 'string' &&
              typeof a.name === 'string' &&
              typeof a.email === 'string' &&
              typeof a.password === 'string' &&
              ['ADMIN', 'COORDENADOR', 'PROFESSOR'].includes(a.role)
          )
        ) as T
      }

      if (key === 'grade.session') {
        if (
          !parsed ||
          typeof parsed !== 'object' ||
          typeof (parsed as Account).id !== 'string'
        ) {
          return fallback
        }
      }

      if (key === 'grade.data') {
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
          return fallback
        }
        const source = parsed as Record<string, unknown>
        const safeRows = (val: unknown): Row[] =>
          Array.isArray(val)
            ? val
                .filter(
                  item =>
                    item &&
                    typeof item === 'object' &&
                    typeof (item as Row).id === 'string'
                )
                .map(
                  item =>
                    Object.fromEntries(
                      Object.entries(item as Row).map(([k, v]) => [
                        k,
                        String(v ?? ''),
                      ])
                    ) as Row
                )
            : []

        return {
          academic: safeRows(source.academic),
          slots: safeRows(source.slots),
          allocations: safeRows(source.allocations),
          availability: safeRows(source.availability),
        } as T
      }

      return parsed as T
    } catch {
      return fallback
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      /* Mantém a tela utilizável se o navegador bloquear o armazenamento. */
    }
  }, [key, value])

  return [value, setValue]
}
