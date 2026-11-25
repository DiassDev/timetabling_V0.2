import {
  Activity,
  BookOpen,
  CalendarDays,
  Check,
  ChevronRight,
  Clock3,
  GraduationCap,
  Settings2,
  Sparkles,
  Users,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { labels } from '../shared/constants'
import type {
  Account,
  Data,
  GenerationResult,
  Role,
  Screen,
} from '../shared/types'

type DashboardProps = {
  role: Role
  data: Data
  accounts: Account[]
  generationResult: GenerationResult | null
  isGenerating: boolean
  onGenerateSchedule: () => void
  onNavigate: (s: Screen) => void
}

export function Dashboard({
  role,
  data,
  accounts,
  generationResult,
  isGenerating,
  onGenerateSchedule,
  onNavigate,
}: DashboardProps) {
  const items: [string, string, Screen, LucideIcon][] =
    role === 'ADMIN'
      ? [
          [
            'Slots de horário',
            'Defina os dias e os horários das aulas.',
            'Slots de horário',
            Settings2,
          ],
          [
            'Estrutura acadêmica',
            'Cadastre cursos, turmas e matérias.',
            'Estrutura acadêmica',
            GraduationCap,
          ],
          ['Usuários', 'Gerencie os acessos da escola.', 'Usuários', Users],
        ]
      : role === 'COORDENADOR'
        ? [
            [
              'Alocações',
              'Escolha horário, matéria, professor e turma.',
              'Alocações',
              BookOpen,
            ],
            [
              'Disponibilidade',
              'Confira os horários disponíveis da equipe.',
              'Disponibilidade',
              Clock3,
            ],
            [
              'Horários',
              'Consulte as aulas organizadas na semana.',
              'Horários',
              CalendarDays,
            ],
          ]
        : [
            [
              'Disponibilidade',
              'Informe quando pode dar aulas.',
              'Disponibilidade',
              Clock3,
            ],
            [
              'Horários',
              'Consulte sua grade da semana.',
              'Horários',
              CalendarDays,
            ],
          ]

  const metricas = generationResult?.metricas
  const falhou = generationResult?.status === 'FALHA'
  const concluida = generationResult?.status === 'CONCLUIDA'

  return (
    <>
      <section className="stats">
        <article>
          <i className="ib">
            <CalendarDays size={17} />
          </i>
          <span>
            Alocações
            <strong>
              {data.allocations.length}
              <small> registradas</small>
            </strong>
          </span>
          <b className="good">
            <Activity size={13} />
            {concluida
              ? `${generationResult.grade.length} aulas geradas`
              : data.allocations.length
                ? 'Em andamento'
                : 'Comece aqui'}
          </b>
        </article>

        <article>
          <i className="iv">
            <Users size={17} />
          </i>
          <span>
            Professores
            <strong>
              {accounts.filter(a => a.role === 'PROFESSOR').length}
              <small> cadastrados</small>
            </strong>
          </span>
          <b className="avatars">
            {role === 'ADMIN' ? 'Equipe' : labels[role]}
          </b>
        </article>

        <article>
          <i className="ig">
            <Check size={17} />
          </i>
          <span>
            Horários-base
            <strong>
              {data.slots.length}
              <small> cadastrados</small>
            </strong>
          </span>
          <b className="ok">
            {data.slots.length ? 'Configurados' : 'A configurar'}
          </b>
        </article>
      </section>

      <div className="dashboard-grid">
        <section className="welcome-card">
          <div className="welcome-art">
            <Sparkles size={25} />
          </div>
          <p>MOTOR DE OTIMIZAÇÃO (AG + SA)</p>
          <h2>Organize a rotina da escola com clareza.</h2>
          <span>
            Gere a grade automaticamente respeitando disponibilidade docente e
            minimizando janelas vagas.
          </span>
          <div className="actions" style={{ marginTop: 15 }}>
            {role !== 'PROFESSOR' && (
              <button
                className="btn primary"
                onClick={onGenerateSchedule}
                disabled={isGenerating}
              >
                <Sparkles size={15} />
                {isGenerating ? 'Gerando...' : 'Gerar grade de horários'}
              </button>
            )}
            <button
              className="btn secondary"
              onClick={() =>
                onNavigate(
                  role === 'ADMIN'
                    ? 'Slots de horário'
                    : role === 'PROFESSOR'
                      ? 'Disponibilidade'
                      : 'Estrutura acadêmica'
                )
              }
            >
              Cadastros <ChevronRight size={15} />
            </button>
          </div>
        </section>

        <section className="quick-card">
          <h2>Acesso rápido</h2>
          {items.map(([label, sub, target, Icon]) => (
            <button
              className="quick-item"
              key={label}
              onClick={() => onNavigate(target)}
            >
              <i>
                <Icon size={16} />
              </i>
              <span>
                <strong>{label}</strong>
                <small>{sub}</small>
              </span>
              <ChevronRight size={15} />
            </button>
          ))}
        </section>
      </div>

      {generationResult && (
        <section
          className="insight"
          style={
            falhou
              ? {
                  background: '#fff2f3',
                  borderColor: '#f4dfe1',
                  color: '#b64c5b',
                }
              : undefined
          }
        >
          <div>
            <strong>
              {concluida
                ? `Última geração concluída · ${generationResult.grade.length} aulas distribuídas sem conflitos`
                : 'Inviabilidade detectada na geração da grade'}
            </strong>
            <p>
              {concluida && metricas
                ? `Violações fortes: ${metricas.violacoes_fortes} · Janelas (professor: ${metricas.janelas_professor}, turma: ${metricas.janelas_turma}) · Tempo: ${metricas.tempo_execucao_segundos}s`
                : generationResult.diagnosticos
                    .map(d => d.mensagem)
                    .join(' | ') ||
                  'Ajuste os cadastros e tente gerar novamente.'}
            </p>
          </div>
          <button onClick={() => onNavigate('Horários')}>
            Ver grade <ChevronRight size={14} />
          </button>
        </section>
      )}

      <section className="next-card">
        <div>
          <strong>Próximos passos</strong>
          <p>
            {role === 'ADMIN'
              ? 'Defina os horários-base e cadastre os acessos da equipe.'
              : role === 'COORDENADOR'
                ? 'Confira as turmas, cadastre as alocações e acione a geração da grade.'
                : 'Informe sua disponibilidade para ajudar na organização.'}
          </p>
        </div>
        <button
          onClick={() =>
            onNavigate(
              role === 'ADMIN'
                ? 'Slots de horário'
                : role === 'COORDENADOR'
                  ? 'Alocações'
                  : 'Disponibilidade'
            )
          }
        >
          Abrir <ChevronRight size={14} />
        </button>
      </section>
    </>
  )
}
