import { useCallback, useEffect, useMemo, useState } from 'react'
import { Login } from './components/auth/Login'
import { Footer } from './components/layout/Footer'
import { Header } from './components/layout/Header'
import { PageHeader } from './components/layout/PageHeader'
import { Sidebar } from './components/layout/Sidebar'
import { EditorModal } from './components/modals/EditorModal'
import { api, toGenerationResult } from './components/shared/api'
import type { ServerState } from './components/shared/api'
import { emptyData, labels } from './components/shared/constants'
import type {
  Account,
  Data,
  GenerationResult,
  Role,
  Row,
  Screen,
} from './components/shared/types'
import {
  id,
  resolveAcademicName,
  resolveProfessorName,
  sectionFor,
  toMinutes,
  useStoredState,
} from './components/shared/utils'
import { Toast } from './components/ui/Toast'
import { Availability } from './components/views/Availability'
import { Dashboard } from './components/views/Dashboard'
import { RecordsTable } from './components/views/RecordsTable'
import { Schedule } from './components/views/Schedule'
import { UsersManagement } from './components/views/UsersManagement'

export default function App() {
  // Dados vêm do banco via API; apenas a sessão fica guardada no navegador.
  const [accounts, setAccounts] = useState<Account[]>([])
  const [data, setData] = useState<Data>(emptyData)
  const [periodoLetivoId, setPeriodoLetivoId] = useState<number | null>(null)
  const [generationResult, setGenerationResult] =
    useState<GenerationResult | null>(null)
  const [session, setSession] = useStoredState<Account | null>(
    'grade.session',
    null
  )
  const [loaded, setLoaded] = useState(false)
  const [loadError, setLoadError] = useState('')

  const [screen, setScreen] = useState<Screen>('Horários')
  const [screenHistory, setScreenHistory] = useState<Screen[]>([])
  const [toast, setToast] = useState('')
  const [mobile, setMobile] = useState(false)
  const [editor, setEditor] = useState<Row | null>(null)
  const [search, setSearch] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginRole, setLoginRole] = useState<Role>('COORDENADOR')
  const [isGenerating, setIsGenerating] = useState(false)

  const notify = (message: string) => {
    setToast(message)
    window.setTimeout(() => setToast(''), 3200)
  }

  const applyState = useCallback((state: ServerState) => {
    setAccounts(state.accounts)
    setData({
      slots: state.slots,
      academic: state.academic,
      allocations: state.allocations,
      availability: state.availability,
    })
    setPeriodoLetivoId(state.periodoLetivoId)
    setGenerationResult(state.generation)
  }, [])

  const reload = useCallback(async () => {
    try {
      applyState(await api.loadState())
      setLoadError('')
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoaded(true)
    }
  }, [applyState])

  useEffect(() => {
    reload()
  }, [reload])

  // Executa uma alteração na API e aplica o estado devolvido pelo servidor.
  const mutate = async (
    action: () => Promise<ServerState>,
    success: string
  ): Promise<boolean> => {
    try {
      applyState(await action())
      if (success) notify(success)
      return true
    } catch (err) {
      notify(err instanceof Error ? err.message : String(err))
      return false
    }
  }

  const active = session && accounts.find(a => a.id === session.id)
  const role = active?.role
  const isFirst = loaded && !loadError && !accounts.some(a => a.role === 'ADMIN')

  const go = (next: Screen) => {
    if (next !== screen) setScreenHistory(old => [...old, screen])
    setScreen(next)
    setMobile(false)
    setSearch('')
  }

  const goBack = () => {
    const previous = screenHistory[screenHistory.length - 1]
    if (!previous) return
    setScreenHistory(old => old.slice(0, -1))
    setScreen(previous)
    setMobile(false)
    setSearch('')
  }

  const createAccount = async (account: Account) => {
    try {
      const { account: created, state } = await api.createAccount({
        email: account.email,
        password: account.password || '',
        role: account.role,
      })
      applyState(state)
      setSession(created)
      setScreen('Horários')
      notify('Acesso criado. A grade da escola já está disponível.')
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : String(err))
    }
  }

  const logout = () => {
    setSession(null)
    setScreenHistory([])
    setLoginError('')
  }

  const resetAll = () => {
    if (role !== 'ADMIN') return
    const confirmed = window.confirm(
      'Isso encerrará a sessão e limpará as informações guardadas neste navegador. Os cadastros do banco de dados serão mantidos. Deseja continuar?'
    )
    if (!confirmed) return
    ;[
      'grade.accounts',
      'grade.data',
      'grade.session',
      'grade.generation',
      'grade.admin_setup_completed',
    ].forEach(key => localStorage.removeItem(key))
    setSession(null)
    setScreen('Horários')
    setScreenHistory([])
    setEditor(null)
    setSearch('')
    reload()
    notify('Navegador limpo. Entre novamente para continuar.')
  }

  const deleteRow = (section: keyof Data, rowId: string) =>
    mutate(() => api.deleteRow(section, rowId), 'Registro removido.')

  const deleteAccount = (accountId: string) =>
    mutate(() => api.deleteAccount(accountId), 'Acesso removido.')

  const ownAvailability =
    role === 'PROFESSOR'
      ? data.availability.filter(a => a.email === active?.email)
      : data.availability

  const visibleRows = useMemo(() => {
    const section = sectionFor(screen)
    const rows = section
      ? screen === 'Disponibilidade'
        ? ownAvailability
        : data[section]
      : []

    const term = search.trim().toLowerCase()
    return term
      ? rows.filter(row =>
          Object.values(row).some(v => String(v).toLowerCase().includes(term))
        )
      : rows
  }, [screen, data, ownAvailability, search])

  if (!loaded) {
    return (
      <div className="app-error">
        <section>
          <p>Carregando dados da escola…</p>
        </section>
      </div>
    )
  }

  if (loadError && !active) {
    return (
      <div className="app-error">
        <section>
          <h1>Servidor indisponível</h1>
          <p>{loadError}</p>
          <button onClick={reload}>Tentar novamente</button>
        </section>
      </div>
    )
  }

  if (!active) {
    return (
      <Login
        first={isFirst}
        accounts={accounts}
        onCreate={createAccount}
        onLogin={async (email, password, wanted) => {
          try {
            const found = await api.login(email, password, wanted)
            setSession(found)
            setScreen('Horários')
            setLoginError('')
          } catch (err) {
            const body = (err as Error & {
              body?: { motivo?: string; papel?: Role }
            }).body
            if (body?.motivo === 'email') {
              setLoginError(
                'Não encontramos esse e-mail. Peça ao administrador para criar seu acesso.'
              )
            } else if (body?.motivo === 'perfil' && body.papel) {
              setLoginError(
                `Este e-mail está cadastrado como ${labels[body.papel]}. Escolha esse perfil para entrar.`
              )
            } else if (body?.motivo === 'senha') {
              setLoginError(
                'A senha não confere. Tente novamente ou peça ajuda ao administrador.'
              )
            } else {
              setLoginError(err instanceof Error ? err.message : String(err))
            }
          }
        }}
        error={loginError}
        role={loginRole}
        setRole={setLoginRole}
      />
    )
  }

  const addAction =
    screen === 'Alocações'
      ? 'Nova alocação'
      : screen === 'Estrutura acadêmica'
        ? 'Novo cadastro'
        : screen === 'Slots de horário'
          ? 'Novo slot'
          : ''

  const createNew = () => {
    if (screen === 'Slots de horário' && role === 'PROFESSOR') {
      notify(
        'Somente o administrador e a coordenação podem alterar os horários-base.'
      )
      return
    }
    setEditor({ id: '' })
  }

  const handleGenerateSchedule = async () => {
    if (isGenerating || role === 'PROFESSOR') return
    if (!periodoLetivoId) {
      notify('Nenhum período letivo ativo encontrado.')
      return
    }
    setIsGenerating(true)
    try {
      const body = await api.generate(periodoLetivoId, active.id)
      const result = toGenerationResult(body, accounts)!
      setGenerationResult(result)

      if (result.status === 'CONCLUIDA') {
        notify(
          `Grade gerada com sucesso (${result.grade.length} aulas alocadas).`
        )
        if (screen !== 'Horários' && screen !== 'Visão geral') {
          go('Horários')
        }
      } else {
        notify(
          result.diagnosticos[0]?.mensagem ||
            'Não foi possível gerar a grade com as restrições atuais.'
        )
      }
    } catch (err) {
      notify(
        err instanceof Error
          ? err.message
          : 'Erro ao comunicar com o motor de geração.'
      )
    } finally {
      setIsGenerating(false)
    }
  }

  const exportSchedule = () => {
    const hasGenerated =
      generationResult?.status === 'CONCLUIDA' &&
      generationResult.grade.length > 0

    const lines = [
      ['Dia', 'Início', 'Turno', 'Matéria', 'Professor', 'Turma'],
      ...(hasGenerated
        ? generationResult.grade
            .filter(
              g =>
                role !== 'PROFESSOR' ||
                g.professorEmail.toLowerCase() === active.email.toLowerCase()
            )
            .map(g => [
              g.dia,
              g.inicio,
              g.turno,
              g.materia,
              g.professor,
              g.turma,
            ])
        : (role === 'PROFESSOR'
            ? data.allocations.filter(a => a.professor === active.email)
            : data.allocations
          ).map(a => {
            const slot = data.slots.find(s => s.id === a.slotId)
            return [
              slot?.dia || '',
              slot?.inicio || '',
              slot?.turno || '',
              resolveAcademicName(data, a.materia),
              resolveProfessorName(accounts, a.professor),
              resolveAcademicName(data, a.turma),
            ]
          })),
    ]

    const csv = lines
      .map(line =>
        line.map(v => `"${String(v).replaceAll('"', '""')}"`).join(';')
      )
      .join('\n')

    const url = URL.createObjectURL(
      new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    )
    const a = document.createElement('a')
    a.href = url
    a.download = 'horario-escolar.csv'
    a.click()
    URL.revokeObjectURL(url)
    notify('Arquivo de horários baixado.')
  }

  const handleSaveEditor = async (row: Row) => {
    if (screen === 'Usuários') {
      if (
        accounts.some(a => a.email.toLowerCase() === row.email.toLowerCase())
      ) {
        notify('Já existe um acesso com este e-mail.')
        return
      }
      try {
        const { state } = await api.createAccount({
          email: row.email,
          password: row.password,
          role: row.role as Role,
        })
        applyState(state)
        setEditor(null)
        notify('Acesso criado com sucesso.')
      } catch (err) {
        notify(err instanceof Error ? err.message : String(err))
      }
      return
    }

    const section = sectionFor(screen)
    if (!section) return

    if (section === 'slots' && active.role === 'PROFESSOR') {
      notify(
        'Somente o administrador e a coordenação podem alterar os horários-base.'
      )
      return
    }

    if (section === 'slots') {
      const start = toMinutes(row.inicio)
      const end = start + Number(row.duracao || 0)
      const overlap = data.slots.some(
        s =>
          s.id !== row.id &&
          s.dia === row.dia &&
          s.turno === row.turno &&
          start < toMinutes(s.inicio) + Number(s.duracao) &&
          toMinutes(s.inicio) < end
      )
      if (overlap) {
        notify(
          'Esse horário se sobrepõe a outro. Escolha outro início ou duração.'
        )
        return
      }
    }

    const isNew = !data[section].some(x => x.id === row.id)
    const saved = await mutate(
      () => api.saveRow(section, row, isNew),
      'Informações salvas.'
    )
    if (saved) setEditor(null)
  }

  return (
    <div className="app">
      <Sidebar
        active={active}
        screen={screen}
        mobile={mobile}
        allocationsCount={
          generationResult?.status === 'CONCLUIDA' &&
          generationResult.grade.length > 0
            ? generationResult.grade.length
            : data.allocations.length
        }
        onNavigate={go}
        onCloseMobile={() => setMobile(false)}
        onHelp={() => notify('Converse com a equipe responsável pela escola.')}
        onLogout={logout}
      />

      <main>
        <Header
          screen={screen}
          role={active.role}
          canGoBack={screenHistory.length > 0}
          search={search}
          isGenerating={isGenerating}
          onSearchChange={setSearch}
          onGoBack={goBack}
          onOpenMobileMenu={() => setMobile(true)}
          onGenerateSchedule={handleGenerateSchedule}
          onLogout={logout}
        />

        <div className="content">
          <PageHeader
            screen={screen}
            active={active}
            addAction={addAction}
            onExportSchedule={exportSchedule}
            onCreateNew={createNew}
          />

          {screen === 'Visão geral' ? (
            <Dashboard
              role={active.role}
              data={data}
              accounts={accounts}
              generationResult={generationResult}
              isGenerating={isGenerating}
              onGenerateSchedule={handleGenerateSchedule}
              onNavigate={go}
            />
          ) : screen === 'Horários' ? (
            <Schedule
              data={data}
              accounts={accounts}
              role={active.role}
              email={active.email}
              generationResult={generationResult}
              onExport={exportSchedule}
            />
          ) : screen === 'Disponibilidade' ? (
            <Availability
              data={data}
              accounts={accounts}
              role={active.role}
              email={active.email}
              onChange={availability => {
                if (active.role !== 'PROFESSOR') return
                const slotIds = availability
                  .filter(a => a.email === active.email)
                  .map(a => a.slotId)
                mutate(() => api.setAvailability(active.email, slotIds), '')
              }}
            />
          ) : screen === 'Usuários' ? (
            <UsersManagement
              accounts={accounts}
              onResetAll={resetAll}
              onCreateRole={targetRole =>
                setEditor({ id: id(), role: targetRole })
              }
              onDeleteAccount={deleteAccount}
            />
          ) : (
            <RecordsTable
              screen={screen}
              rows={visibleRows}
              data={data}
              accounts={accounts}
              role={active.role}
              onEdit={row => setEditor(row)}
              onDelete={row => {
                const section = sectionFor(screen)
                if (section) deleteRow(section, row.id)
              }}
              onAvailabilityCreate={() => {
                setEditor({ id: '', email: active.email })
              }}
            />
          )}

          <Footer />
        </div>
      </main>

      {editor && (
        <EditorModal
          screen={screen}
          row={editor}
          data={data}
          accounts={accounts}
          role={active.role}
          onClose={() => setEditor(null)}
          onSave={handleSaveEditor}
        />
      )}

      <Toast message={toast} />
    </div>
  )
}
