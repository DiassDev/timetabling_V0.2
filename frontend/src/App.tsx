import { useMemo, useState } from 'react'
import { Login } from './components/auth/Login'
import { Footer } from './components/layout/Footer'
import { Header } from './components/layout/Header'
import { PageHeader } from './components/layout/PageHeader'
import { Sidebar } from './components/layout/Sidebar'
import { EditorModal } from './components/modals/EditorModal'
import { requestScheduleGeneration } from './components/shared/api'
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
import { Dashboard } from './components/views/Dashboard'
import { RecordsTable } from './components/views/RecordsTable'
import { Schedule } from './components/views/Schedule'
import { UsersManagement } from './components/views/UsersManagement'

export default function App() {
  const [accounts, setAccounts] = useStoredState<Account[]>(
    'grade.accounts',
    []
  )
  const [data, setData] = useStoredState<Data>('grade.data', emptyData)
  const [session, setSession] = useStoredState<Account | null>(
    'grade.session',
    null
  )
  const [generationResult, setGenerationResult] =
    useStoredState<GenerationResult | null>('grade.generation', null)
  const [adminSetupRequired, setAdminSetupRequired] = useState(
    () => localStorage.getItem('grade.admin_setup_completed') !== 'true'
  )

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

  const active = session && accounts.find(a => a.id === session.id)
  const role = active?.role
  const isFirst =
    adminSetupRequired || !accounts.some(account => account.role === 'ADMIN')

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

  const createAccount = (account: Account) => {
    if (account.role === 'ADMIN') {
      setAccounts(old => [...old.filter(existing => existing.role !== 'ADMIN'), account])
      localStorage.setItem('grade.admin_setup_completed', 'true')
      setAdminSetupRequired(false)
    } else {
      setAccounts(old => [...old, account])
    }
    setSession(account)
    setScreen('Horários')
    notify('Acesso criado. A grade da escola já está disponível.')
  }

  const logout = () => {
    setSession(null)
    setScreenHistory([])
    setLoginError('')
  }

  const resetAll = () => {
    if (role !== 'ADMIN') return
    const confirmed = window.confirm(
      'Isso apagará todos os acessos e todos os horários e cadastros salvos neste navegador. Essa ação não pode ser desfeita. Deseja recomeçar do zero?'
    )
    if (!confirmed) return

    ;[
      'grade.accounts',
      'grade.data',
      'grade.session',
      'grade.generation',
      'grade.admin_setup_completed',
    ].forEach(key => localStorage.removeItem(key))
    setAccounts([])
    setData(emptyData)
    setGenerationResult(null)
    setAdminSetupRequired(true)
    setSession(null)
    setScreen('Horários')
    setScreenHistory([])
    setEditor(null)
    setSearch('')
    notify('Tudo foi limpo. Cadastre o administrador para começar novamente.')
  }

  const saveRow = (section: keyof Data, row: Row) => {
    setData(old => ({
      ...old,
      [section]: old[section].some(x => x.id === row.id)
        ? old[section].map(x => (x.id === row.id ? row : x))
        : [...old[section], row],
    }))
    setEditor(null)
    notify('Informações salvas.')
  }

  const deleteRow = (section: keyof Data, rowId: string) => {
    setData(old => ({
      ...old,
      [section]: old[section].filter(x => x.id !== rowId),
    }))
    notify('Registro removido.')
  }

  const deleteAccount = (accountId: string) => {
    setAccounts(old => old.filter(a => a.id !== accountId))
    notify('Acesso removido.')
  }

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
          Object.values(row).some(v => v.toLowerCase().includes(term))
        )
      : rows
  }, [screen, data, ownAvailability, search])

  if (!active) {
    return (
      <Login
        first={isFirst}
        accounts={accounts}
        onCreate={createAccount}
        onLogin={(email, password, wanted) => {
          const byEmail = accounts.find(
            a => a.email.toLowerCase() === email.trim().toLowerCase()
          )
          const found =
            byEmail && byEmail.password === password && byEmail.role === wanted
              ? byEmail
              : null

          if (found) {
            setSession(found)
            setScreen('Horários')
            setLoginError('')
          } else if (!byEmail && accounts.length === 0) {
            setLoginError(
              'Ainda não há acesso cadastrado. Use “Primeiro acesso” para começar.'
            )
          } else if (!byEmail) {
            setLoginError(
              'Não encontramos esse e-mail. Peça ao administrador para criar seu acesso.'
            )
          } else if (byEmail.role !== wanted) {
            setLoginError(
              `Este e-mail está cadastrado como ${labels[byEmail.role]}. Escolha esse perfil para entrar.`
            )
          } else {
            setLoginError(
              'A senha não confere. Tente novamente ou peça ajuda ao administrador.'
            )
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
      : screen === 'Disponibilidade'
        ? 'Adicionar horário disponível'
        : screen === 'Estrutura acadêmica'
          ? 'Novo cadastro'
          : screen === 'Slots de horário'
            ? 'Novo slot'
            : ''

  const createNew = () => {
    if (screen === 'Slots de horário' && role !== 'ADMIN') {
      notify('Somente o administrador pode alterar os horários-base.')
      return
    }
    setEditor({ id: id() })
  }

  const handleGenerateSchedule = async () => {
    if (isGenerating) return
    setIsGenerating(true)
    try {
      const { result, syncedData } = await requestScheduleGeneration({
        active,
        accounts,
        data,
      })

      if (syncedData) {
        setData({
          slots: syncedData.slots,
          academic: syncedData.academic,
          allocations: syncedData.allocations,
          availability: syncedData.availability,
        })
        setAccounts(syncedData.accounts)
      }

      setGenerationResult(result)

      if (result.status === 'CONCLUIDA') {
        notify(
          `Grade gerada com sucesso (${result.grade.length} aulas alocadas).`
        )
        if (screen !== 'Horários' && screen !== 'Visão geral') {
          go('Horários')
        }
      } else {
        const msg =
          result.diagnosticos[0]?.mensagem ||
          'Não foi possível gerar a grade com as restrições atuais.'
        notify(msg)
      }
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Erro ao comunicar com o motor de geração.'
      notify(msg)
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

  const handleSaveEditor = (row: Row) => {
    if (screen === 'Usuários') {
      if (
        accounts.some(
          a => a.email.toLowerCase() === row.email.toLowerCase()
        )
      ) {
        notify('Já existe um acesso com este e-mail.')
        return
      }
      const account: Account = {
        id: row.id,
        name: row.name,
        email: row.email,
        password: row.password,
        role: row.role as Role,
      }
      setAccounts(old => [...old, account])
      setEditor(null)
      notify('Acesso criado com sucesso.')
      return
    }

    const section = sectionFor(screen)
    if (!section) return

    if (section === 'slots' && active.role !== 'ADMIN') {
      notify('Somente o administrador pode alterar os horários-base.')
      return
    }

    if (
      section === 'availability' &&
      active.role === 'PROFESSOR' &&
      row.email !== active.email
    ) {
      notify('Você só pode alterar sua própria disponibilidade.')
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

    if (section === 'allocations' && row.slotId) {
      const duplicate = data.allocations.some(
        a =>
          a.id !== row.id &&
          Boolean(a.slotId) &&
          a.slotId === row.slotId &&
          (a.professor === row.professor || a.turma === row.turma)
      )
      if (duplicate) {
        notify(
          'Esse horário já está ocupado pelo professor ou pela turma.'
        )
        return
      }
    }

    if (section === 'availability') {
      const duplicate = data.availability.some(
        a =>
          a.id !== row.id &&
          a.email === row.email &&
          a.slotId === row.slotId
      )
      if (duplicate) {
        notify(
          'Esse professor já informou disponibilidade nesse horário.'
        )
        return
      }
    }

    saveRow(section, row)
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
                setEditor({ id: id(), email: active.email })
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
