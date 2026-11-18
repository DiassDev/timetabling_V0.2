import {
  BookOpen,
  CalendarDays,
  Clock3,
  GraduationCap,
  LayoutDashboard,
  Settings2,
  Users,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Data, Role, Screen } from './types'

export const labels: Record<Role, string> = {
  ADMIN: 'Administrador',
  COORDENADOR: 'Coordenador',
  PROFESSOR: 'Professor',
}

export const weekDays = [
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
]

export const screens: Record<Role, Array<[Screen, LucideIcon]>> = {
  ADMIN: [
    ['Visão geral', LayoutDashboard],
    ['Horários', CalendarDays],
    ['Estrutura acadêmica', GraduationCap],
    ['Usuários', Users],
    ['Slots de horário', Settings2],
  ],
  COORDENADOR: [
    ['Visão geral', LayoutDashboard],
    ['Horários', CalendarDays],
    ['Alocações', BookOpen],
    ['Disponibilidade', Clock3],
    ['Estrutura acadêmica', GraduationCap],
  ],
  PROFESSOR: [
    ['Horários', CalendarDays],
    ['Disponibilidade', Clock3],
  ],
}

export const emptyData: Data = {
  academic: [],
  slots: [],
  allocations: [],
  availability: [],
}
