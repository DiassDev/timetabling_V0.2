import type { Account, Data, GenerationResult, Row } from './types'

export type SyncedPayload = {
  slots: Row[]
  academic: Row[]
  allocations: Row[]
  availability: Row[]
  accounts: Account[]
}

export type GenerateScheduleResponse = {
  result: GenerationResult
  syncedData?: SyncedPayload
}

const API_ENDPOINTS = [
  '/api/execucoes/gerar/',
  'http://127.0.0.1:8000/api/execucoes/gerar/',
]

export async function requestScheduleGeneration(params: {
  active: Account
  accounts: Account[]
  data: Data
}): Promise<GenerateScheduleResponse> {
  const payload = {
    solicitado_por: {
      id: params.active.id,
      name: params.active.name,
      email: params.active.email,
      role: params.active.role,
    },
    accounts: params.accounts,
    slots: params.data.slots,
    academic: params.data.academic,
    availability: params.data.availability,
    allocations: params.data.allocations,
  }

  let lastError: Error | null = null

  for (const url of API_ENDPOINTS) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (response.status !== 201 && response.status !== 422) {
        continue
      }

      const body = await response.json()
      const result: GenerationResult = {
        id: body.id,
        status: body.status === 'CONCLUIDA' ? 'CONCLUIDA' : 'FALHA',
        algoritmo: body.algoritmo || 'AG_SA_HIBRIDO',
        concluida_em: body.concluida_em,
        grade: Array.isArray(body.grade) ? body.grade : [],
        metricas: body.metricas || null,
        diagnosticos: Array.isArray(body.diagnosticos) ? body.diagnosticos : [],
      }

      return {
        result,
        syncedData: body.dados_sincronizados,
      }
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err))
    }
  }

  throw (
    lastError ||
    new Error(
      'Não foi possível conectar ao servidor da API. Verifique se o backend Django está em execução.'
    )
  )
}
