import type { Account, Data, GenerationResult, Role, Row } from './types'

// Cliente da API Django: todas as telas leem e gravam pelo banco através de /api/ui/.

export type ServerState = Data & {
  accounts: Account[]
  periodoLetivoId: number | null
  generation: GenerationResult | null
}

type RawState = Data & {
  accounts: Account[]
  periodo_letivo: { id: number; rotulo: string } | null
  ultima_execucao: Record<string, unknown> | null
}

const BASE = '/api'

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(BASE + path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    })
  } catch {
    throw new Error(
      'Não foi possível conectar ao servidor. Verifique se o backend está em execução.'
    )
  }
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(body.detail || 'Não foi possível concluir a ação.')
    ;(error as Error & { body?: unknown }).body = body
    throw error
  }
  return body as T
}

const json = (method: string, payload?: unknown): RequestInit => ({
  method,
  body: payload === undefined ? undefined : JSON.stringify(payload),
})

// Converte a execução retornada pelo backend no resultado exibido pelas telas.
export function toGenerationResult(
  body: Record<string, unknown> | null,
  accounts: Account[]
): GenerationResult | null {
  if (!body) return null
  const names = new Map(accounts.map(a => [a.email.toLowerCase(), a.name]))
  const grade = (Array.isArray(body.grade) ? body.grade : []).map(
    (g: GenerationResult['grade'][number]) => ({
      ...g,
      professor: names.get(String(g.professorEmail).toLowerCase()) || g.professor,
    })
  )
  return {
    id: body.id as number,
    status: body.status === 'CONCLUIDA' ? 'CONCLUIDA' : 'FALHA',
    algoritmo: (body.algoritmo as string) || 'AG_SA_HIBRIDO',
    concluida_em: body.concluida_em as string,
    grade,
    metricas: (body.metricas as GenerationResult['metricas']) || null,
    diagnosticos: Array.isArray(body.diagnosticos) ? body.diagnosticos : [],
  }
}

function toState(raw: RawState): ServerState {
  return {
    accounts: raw.accounts,
    slots: raw.slots,
    academic: raw.academic,
    allocations: raw.allocations,
    availability: raw.availability,
    periodoLetivoId: raw.periodo_letivo?.id ?? null,
    generation: toGenerationResult(raw.ultima_execucao, raw.accounts),
  }
}

export const api = {
  loadState: async () => toState(await call<RawState>('/ui/estado/')),

  // Retorna a conta ou lança erro com `motivo` ('email' | 'senha' | 'perfil').
  login: (email: string, password: string, role: Role) =>
    call<Account>('/ui/login/', json('POST', { email, password, role })),

  createAccount: async (account: { email: string; password: string; role: Role }) => {
    const raw = await call<RawState & { conta: Account }>(
      '/ui/contas/',
      json('POST', account)
    )
    return { account: raw.conta, state: toState(raw) }
  },

  deleteAccount: async (id: string) =>
    toState(await call<RawState>(`/ui/contas/${id}/`, json('DELETE'))),

  saveRow: async (section: keyof Data, row: Row, isNew: boolean) =>
    toState(
      await call<RawState>(
        isNew
          ? `/ui/registros/${section}/`
          : `/ui/registros/${section}/${encodeURIComponent(row.id)}/`,
        json(isNew ? 'POST' : 'PUT', row)
      )
    ),

  deleteRow: async (section: keyof Data, id: string) =>
    toState(
      await call<RawState>(
        `/ui/registros/${section}/${encodeURIComponent(id)}/`,
        json('DELETE')
      )
    ),

  setAvailability: async (email: string, slotIds: string[]) =>
    toState(
      await call<RawState>('/ui/disponibilidade/', json('PUT', { email, slotIds }))
    ),

  // Gera a grade a partir do banco (período letivo ativo); 422 indica inviabilidade.
  generate: async (periodoLetivoId: number, solicitadoPorId: string) => {
    const response = await fetch(BASE + '/execucoes/gerar/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        periodo_letivo_id: periodoLetivoId,
        solicitado_por_id: Number(solicitadoPorId),
      }),
    }).catch(() => {
      throw new Error('Não foi possível conectar ao servidor de geração.')
    })
    if (response.status !== 201 && response.status !== 422) {
      throw new Error('Erro ao comunicar com o motor de geração.')
    }
    return (await response.json()) as Record<string, unknown>
  },
}
