"""Orquestrador híbrido (Algoritmo Genético + Simulated Annealing) para geração de horários."""

import random
import time
from dataclasses import dataclass

from .avaliador import PesosAvaliacao, avaliar_solucao
from .dominio import (
    ContextoExecucao,
    InstanciaTimetabling,
    ItemGrade,
    ResultadoOtimizacao,
)
from .genetico import ConfiguracaoAG, executar_algoritmo_genetico
from .simulated_annealing import ConfiguracaoSA, executar_simulated_annealing
from .validador import construir_contexto


@dataclass(frozen=True)
class ConfiguracaoMotor:
    """Configuração unificada do motor híbrido de otimização."""

    ag: ConfiguracaoAG = ConfiguracaoAG()
    sa: ConfiguracaoSA = ConfiguracaoSA()
    pesos: PesosAvaliacao = PesosAvaliacao()
    semente: int | None = None


def gerar_horario(
    instancia: InstanciaTimetabling,
    config: ConfiguracaoMotor = ConfiguracaoMotor(),
) -> ResultadoOtimizacao:
    """Executa a geração do zero: valida viabilidade, evolui com AG e refina com SA."""
    inicio = time.perf_counter()
    contexto = construir_contexto(instancia)
    rng = random.Random(config.semente)

    def avaliador(cromossomo, ctx):
        return avaliar_solucao(cromossomo, ctx, config.pesos)

    melhor_ag, metrica_ag, hist_ag = executar_algoritmo_genetico(
        contexto=contexto,
        config=config.ag,
        rng=rng,
        avaliador=avaliador,
    )

    if metrica_ag.custo_total > 0:
        melhor_final, metrica_final, hist_sa = executar_simulated_annealing(
            cromossomo_inicial=melhor_ag,
            contexto=contexto,
            config=config.sa,
            rng=rng,
            avaliador=avaliador,
        )
    else:
        melhor_final, metrica_final, hist_sa = melhor_ag, metrica_ag, [0.0]

    grade = _montar_grade(melhor_final, contexto)
    duracao = time.perf_counter() - inicio

    return ResultadoOtimizacao(
        grade=grade,
        metricas=metrica_final,
        tempo_execucao_segundos=duracao,
        historico_custo_ga=hist_ag,
        historico_custo_sa=hist_sa,
    )


def _montar_grade(cromossomo: list[int], contexto: ContextoExecucao) -> tuple[ItemGrade, ...]:
    """Converte o cromossomo numérico em itens de grade legíveis no domínio."""
    itens = [
        ItemGrade(
            alocacao_id=aula.alocacao_id,
            professor_id=aula.professor_id,
            disciplina_id=aula.disciplina_id,
            turma_id=aula.turma_id,
            slot=contexto.slots[slot_idx],
        )
        for aula, slot_idx in zip(contexto.aulas, cromossomo)
    ]
    itens.sort(
        key=lambda item: (
            item.slot.dia.value,
            item.slot.turno.value,
            item.slot.inicio_minutos,
            item.turma_id,
        )
    )
    return tuple(itens)
