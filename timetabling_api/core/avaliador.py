"""Avaliador ortogonal de restrições fortes (hard) e fracas (soft) para soluções de timetabling."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

from .dominio import ContextoExecucao, DiaSemana, MetricasAvaliacao, Turno


@dataclass(frozen=True)
class PesosAvaliacao:
    """Pesos utilizados para compor a função objetivo única a ser minimizada."""

    restricao_forte: float = 10_000.0
    janela_professor: float = 10.0
    janela_turma: float = 10.0


def avaliar_solucao(
    cromossomo: Sequence[int],
    contexto: ContextoExecucao,
    pesos: PesosAvaliacao = PesosAvaliacao(),
) -> MetricasAvaliacao:
    """Calcula todas as métricas de violações fortes, fracas e custo total de um cromossomo."""
    conflitos_professor = 0
    conflitos_turma = 0
    fora_disponibilidade = 0

    ocupacao_professor: dict[tuple[str, int], int] = defaultdict(int)
    ocupacao_turma: dict[tuple[str, int], int] = defaultdict(int)
    aulas_prof_bloco: dict[tuple[str, tuple[DiaSemana, Turno]], list[int]] = defaultdict(list)
    aulas_turma_bloco: dict[tuple[str, tuple[DiaSemana, Turno]], list[int]] = defaultdict(list)

    aulas = contexto.aulas
    permitidos_set = contexto.slots_permitidos_set
    ordem_slot = contexto.ordem_slot_no_bloco

    for idx_aula, slot_idx in enumerate(cromossomo):
        aula = aulas[idx_aula]
        if slot_idx not in permitidos_set[idx_aula]:
            fora_disponibilidade += 1

        chave_prof = (aula.professor_id, slot_idx)
        ocupacao_professor[chave_prof] += 1
        if ocupacao_professor[chave_prof] > 1:
            conflitos_professor += 1

        chave_turma = (aula.turma_id, slot_idx)
        ocupacao_turma[chave_turma] += 1
        if ocupacao_turma[chave_turma] > 1:
            conflitos_turma += 1

        bloco, pos = ordem_slot[slot_idx]
        aulas_prof_bloco[(aula.professor_id, bloco)].append(pos)
        aulas_turma_bloco[(aula.turma_id, bloco)].append(pos)

    janelas_professor = _contar_janelas(aulas_prof_bloco)
    janelas_turma = _contar_janelas(aulas_turma_bloco)

    violacoes_fortes = conflitos_professor + conflitos_turma + fora_disponibilidade
    custo_total = (
        pesos.restricao_forte * violacoes_fortes
        + pesos.janela_professor * janelas_professor
        + pesos.janela_turma * janelas_turma
    )

    return MetricasAvaliacao(
        conflitos_professor=conflitos_professor,
        conflitos_turma=conflitos_turma,
        fora_disponibilidade=fora_disponibilidade,
        janelas_professor=janelas_professor,
        janelas_turma=janelas_turma,
        custo_total=custo_total,
    )


def _contar_janelas(grupos_posicoes: dict[tuple[str, tuple[DiaSemana, Turno]], list[int]]) -> int:
    """Conta o total de janelas vagas entre a primeira e a última aula de cada bloco."""
    total_janelas = 0
    for posicoes in grupos_posicoes.values():
        if len(posicoes) < 2:
            continue
        unicas = sorted(set(posicoes))
        if len(unicas) >= 2:
            total_janelas += (unicas[-1] - unicas[0] + 1) - len(unicas)
    return total_janelas


def identificar_aulas_em_conflito(
    cromossomo: Sequence[int],
    contexto: ContextoExecucao,
) -> list[int]:
    """Retorna os índices das aulas que participam de algum conflito de professor, turma ou disponibilidade."""
    aulas_por_prof_slot: dict[tuple[str, int], list[int]] = defaultdict(list)
    aulas_por_turma_slot: dict[tuple[str, int], list[int]] = defaultdict(list)
    conflitantes: set[int] = set()

    aulas = contexto.aulas
    permitidos_set = contexto.slots_permitidos_set

    for idx_aula, slot_idx in enumerate(cromossomo):
        aula = aulas[idx_aula]
        if slot_idx not in permitidos_set[idx_aula]:
            conflitantes.add(idx_aula)
        aulas_por_prof_slot[(aula.professor_id, slot_idx)].append(idx_aula)
        aulas_por_turma_slot[(aula.turma_id, slot_idx)].append(idx_aula)

    for lista in aulas_por_prof_slot.values():
        if len(lista) > 1:
            conflitantes.update(lista)

    for lista in aulas_por_turma_slot.values():
        if len(lista) > 1:
            conflitantes.update(lista)

    return list(conflitantes)
