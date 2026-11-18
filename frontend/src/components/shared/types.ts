export type Role = 'ADMIN' | 'COORDENADOR' | 'PROFESSOR'

export type Screen =
  | 'Visão geral'
  | 'Horários'
  | 'Alocações'
  | 'Disponibilidade'
  | 'Estrutura acadêmica'
  | 'Slots de horário'
  | 'Usuários'

export type Account = {
  id: string
  name: string
  email: string
  password: string
  role: Role
}

export type Row = {
  id: string
  [key: string]: string
}

export type Data = {
  academic: Row[]
  slots: Row[]
  allocations: Row[]
  availability: Row[]
}

export type Field = {
  key: string
  label: string
  type: string
  options?: [string, string][]
  required?: boolean
}

export type ScheduledLesson = {
  id: string
  alocacaoId: string
  slotId: string
  dia: string
  turno: string
  inicio: string
  duracao: string
  materia: string
  materiaId: string
  professor: string
  professorEmail: string
  turma: string
  turmaId: string
  curso: string
  aulas: string
}

export type EngineMetrics = {
  conflitos_professor: number
  conflitos_turma: number
  fora_disponibilidade: number
  janelas_professor: number
  janelas_turma: number
  violacoes_fortes: number
  violacoes_fracas: number
  custo_total: number
  tempo_execucao_segundos: number
  valida: boolean
}

export type DiagnosticItem = {
  id?: number
  tipo: string
  mensagem: string
}

export type GenerationResult = {
  id?: number
  status: 'CONCLUIDA' | 'FALHA'
  algoritmo?: string
  concluida_em?: string
  grade: ScheduledLesson[]
  metricas: EngineMetrics | null
  diagnosticos: DiagnosticItem[]
}
